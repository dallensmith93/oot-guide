"""Integrity assertions; does not pretend to validate gameplay facts."""
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from generate import build

def check():
    g=build()
    os=g['objectives']; ss=g['sections']; ids=[o['id'] for o in os]
    assert len(ids)==len(set(ids)), 'Duplicate objective IDs'
    sids=[s['id'] for s in ss]
    assert len(g['episodes'])==25, 'Expected exactly 25 episodes'
    episode_sections=[sid for ep in g['episodes'] for sid in ep['sections']]
    assert episode_sections==sids,'Episodes must cover the whole route once, in order'
    assert len({ep['id'] for ep in g['episodes']})==25
    for ep in g['episodes']:
        assert ep['expected']==next(s['expected'] for s in ss if s['id']==ep['sections'][-1])
    assert len(sids)==len(set(sids)), 'Duplicate route IDs'
    expected={'gs':100,'hp':36,'boss':8}
    for typ,n in expected.items():
        rows=[o for o in os if o['type']==typ]
        assert len(rows)==n,(typ,len(rows),n)
        if typ!='boss': assert len({o['number'] for o in rows})==n
    assert 3+expected['boss']+expected['hp']//4==20
    for typ,n in [('song',13),('bottle',5),('dungeon-map',10),('compass',10)]:
        assert len([o for o in os if o['type']==typ])==n,(typ,n)
    assert {'magic-meter','dins-fire','magic-spin','farore-wind','double-magic','nayru-love','double-defence'}<=set(ids),'Missing fairy reward'
    source_ids={s['id'] for s in g['sources']}
    assert len(source_ids)==len(g['sources']), 'Duplicate source IDs'
    running={'gs':0,'hp':0,'boss':0}
    for s in ss:
        here=[o for o in os if o['section']==s['id']]
        assert s.get('steps'),f"No directions: {s['id']}"
        assert set(s['objectiveIds'])=={o['id'] for o in here}
        for o in here:
            assert o['name'] and o.get('instructions'),f"Empty objective {o['id']}"
            assert isinstance(o.get('requires',[]),list)
            assert o.get('age') and o.get('time'),o['id']
            for sid in o.get('sources',[]): assert sid in source_ids,(o['id'],sid)
            if o['type'] in running: running[o['type']]+=1
        assert s['expected']==dict(running,hearts=3+running['boss']+running['hp']//4)
        for sid in s.get('sources',[]): assert sid in source_ids,(s['id'],sid)
    assert running==expected
    assert sum(len(s['objectiveIds']) for s in ss)==len(os),'Double route placement'
    for o in os: assert o['section'] in sids,o['id']
    # Important known age/order dependencies, asserted independently of totals.
    pos={s['id']:i for i,s in enumerate(ss)}
    acquisition={
        'Bombs':'r07','Boomerang':'r11','Hookshot':'r14','Longshot':'r21',
        'Bottled Bug':'r04','Lenses of Truth':'r16','Lens of Truth':'r16',
        'Megaton Hammer':'r18','Silver Gauntlets':'r29','Golden Gauntlets':'r37',
        'Iron Boots':'r20','Goron Tunic':'r18','Golden Scale':'r22',
        'Bolero of Fire':'r18','Requiem of Spirit':'r28',
        'Song of Storms':'r14','Din\'s Fire':'r08',
        'Planted Graveyard bean':'r12','Planted Lake Hylia bean':'r12',
        'Planted Lost Woods bean':'r12','Planted River bean':'r10',
        'Planted Dodongo entrance bean':'r12','Planted Crater bean':'r29',
        'Planted Colossus bean':'r29','Adult canyon Fairy Thought read':'r14',
        'Adult moat Fairy Thought read':'r14'
    }
    dependency_checks=0
    for o in os:
        for item in o.get('requires',[]):
            if item in acquisition:
                assert pos[o['section']]>=pos[acquisition[item]],f"Prerequisite {item} too early: {o['id']}"
                dependency_checks+=1
        for shared in o.get('sharedObjectiveIds',[]):
            assert shared in ids,(o['id'],'Unknown shared reward',shared)
        if 'Bolero of Fire' in o.get('requires',[]) and o.get('age')=='Child':
            assert pos[o['section']]>pos['r18'],f"Child crater too early: {o['id']}"
        if 'Silver Gauntlets' in o.get('requires',[]) and o['type']=='gs':
            assert pos[o['section']]>=pos['r30'],f"Silver Gauntlets too early: {o['id']}"
        if 'Planted Crater bean' in o.get('requires',[]):
            assert pos[o['section']]>pos['r29'],f"Crater bean too early: {o['id']}"
    config=tomllib.loads((ROOT/'netlify.toml').read_text(encoding='utf-8'))
    assert config['build']['publish']=='site'
    assert not config['build'].get('command'), 'Unexpected build command'
    shell=(ROOT/'site'/'index.html').read_text(encoding='utf-8')
    assets=re.findall(r'(?:src|href)="([^"#]+\.(?:js|css))"',shell)
    for asset in assets:
        assert not asset.startswith(('http:','https:','//')),asset
        assert (ROOT/'site'/asset).is_file(),asset
    assert {'data.js','app.js','styles.css'}<={a.removeprefix('./') for a in assets}
    for file in (ROOT/'content').glob('*.json'):
        raw=file.read_text(encoding='utf-8')
        assert '\ufffd' not in raw,f"Replacement character: {file}"
    assert not list(ROOT.glob('*.zip')),'ZIP forbidden by request'
    print(f'PASS: counts, 20-heart calculation, IDs, route/source links, running totals, {dependency_checks} known-item prerequisite comparisons, shared reward links, deployment configuration, local assets, UTF-8 and no ZIP.')
    return g

if __name__=='__main__': check()
