"""Build deterministic browser data and Markdown from the curated JSON records.

No network or third-party modules. The generated files are committed; Netlify
publishes site/ directly and does not need to run this script.
"""
import json
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def read(name):
    return json.loads((ROOT/'content'/name).read_text(encoding='utf-8'))

def build():
    sections = read('route.json')
    if isinstance(sections,dict):
        sections = sections['sections']
    sources = []
    for name in ('platform-sources.json','collectible-sources.json','route-sources.json'):
        part=read(name)
        if isinstance(part,dict):
            part=part.get('sources',[])
        sources.extend(part)
    sources=list({s['id']:s for s in sources}.values())
    meta=read('meta.json')
    by_section={s['id']:s for s in sections}
    placement={
        'child-forest':'r04','adult-forest':'r15','castle':'r03',
        'child-cleanup':'r12','child-crater':'r29','child-return':'r17',
        'child-valley':'r12','deku':'r02','dodongo':'r07',
        'final-castle':'r36','fire-temple':'r18','forest-temple':'r15',
        'gerudo-archery':'r32','ice-cavern':'r20','jabu':'r11',
        'kakariko-child':'r05','lake-child':'r10','late-cleanup':'r33',
        'mountain-child':'r08','post-fire':'r19','post-jabu':'r12',
        'ranch-child':'r09','shadow-temple':'r25','spirit-adult':'r30',
        'spirit-child':'r29','wasteland':'r28','water-temple':'r21',
        'well':'r16','zora-child':'r10','adult-field':'r24',
        'adult-gerudo':'r27','adult-kakariko':'r14','adult-lake':'r22',
        'adult-mountain':'r19','adult-zora':'r20',
        'token-rewards':'r34','ranch-market-child':'r09','post-spirit-gerudo':'r32'
    }
    objectives=[]
    for s in sections:
        for reward in s.get('rewards',[]):
            o=dict(reward)
            o['section']=s['id']
            o.setdefault('region',s.get('region','Hyrule'))
            o.setdefault('age',s.get('age','Either'))
            o.setdefault('time',s.get('time','Any'))
            o.setdefault('requires',[])
            o.setdefault('sources',s.get('sources',s.get('sourceIds',[])))
            if o.get('core') is False: o['optional']=True
            if o.get('type') in ('boss-container','heart-container'): o['type']='boss'
            if o.get('type')=='temporary':
                o['optional']=True
                o['category']='Temporary trade objects'
            objectives.append(o)
    collectibles=read('collectibles.json')
    if isinstance(collectibles,dict): collectibles=collectibles['collectibles']
    for item in collectibles:
        o=dict(item)
        o['type']={'skulltula':'gs','heart-piece':'hp','heart':'hp'}.get(o['type'],o['type'])
        o['section']=o.get('section',placement.get(o['suggestedStage']))
        if o['id']=='hp-026': o['section']='r30'
        if o['id']=='gs-031': o['section']='r12'
        if o['id']=='gs-061': o['section']='r26'
        o['sources']=o.get('sources',o.get('sourceIds',[]))
        objectives.append(o)
    objectives.extend(read('extras.json'))
    if (ROOT/'content'/'grottos.json').exists():
        objectives.extend(read('grottos.json'))
        sources.extend(read('grotto-sources.json'))
    for o in objectives:
        o.setdefault('sources',o.get('sourceIds',[]))
        if o.get('section') not in by_section: raise ValueError(f"Missing section for {o['id']}: {o.get('section')}")
    # Immutable public IDs; sort within the itinerary without changing identity.
    order={s['id']:i for i,s in enumerate(sections)}
    objectives.sort(key=lambda o:(order[o['section']],0 if o['type'] not in ('gs','hp') else 1,o.get('number',0)))
    # Stable catalogue numbers and chronological collection positions are distinct.
    totals={t:sum(o['type']==t for o in objectives) for t in ('gs','hp','boss','bottle')}
    positions={t:0 for t in totals}
    for o in objectives:
        if o['type'] in totals:
            positions[o['type']]+=1
            o['routeNumber']=positions[o['type']]
            o['collectionTotal']=totals[o['type']]
            o['collectionNumber']=o.get('number',positions[o['type']])
    running={'gs':0,'hp':0,'boss':0}
    for i,s in enumerate(sections):
        s['number']=i+1
        os=[o for o in objectives if o['section']==s['id']]
        s['objectiveIds']=[o['id'] for o in os]
        for o in os:
            if o['type'] in running: running[o['type']]+=1
        s['expected']={**running,'hearts':3+running['boss']+running['hp']//4}
        s['next']=s.get('next') or (sections[i+1]['title'] if i+1<len(sections) else 'Save, export progress, and review optional records.')
    meta['controls'][0]['sources']=['nintendo-developer3','controls-vulkk']
    for c in meta['controls'][1:]: c['sources']=['controls-vulkk','controls-shield','nintendo-product']
    episodes=read('episodes.json')
    for number,episode in enumerate(episodes,1):
        episode['number']=number
        episode['expected']=by_section[episode['sections'][-1]]['expected']
        for sid in episode['sections']:
            by_section[sid]['episode']=episode['id']
            by_section[sid]['episodeNumber']=number
    g={'fairies':read('fairies.json'),'meta':meta,'sections':sections,'episodes':episodes,'objectives':objectives,'sources':sources}
    (ROOT/'site').mkdir(exist_ok=True)
    (ROOT/'site'/'data.js').write_text('/* Generated by scripts/generate.py. Edit content/*.json. */\nwindow.GUIDE = '+json.dumps(g,ensure_ascii=False,indent=2)+';\n',encoding='utf-8')
    export(g)
    print(f"Generated {len(sections)} sections, {len(objectives)} objectives, {len(sources)} sources. Totals: {running}")
    return g

def export(g):
    out=ROOT/'guide';out.mkdir(exist_ok=True)
    refs={s['id']:s for s in g['sources']}
    def citations(ids):
        return ' · '.join(f"[{refs[x]['title']}]({refs[x]['url']})" for x in ids if x in refs)
    def collectible_label(o):
        names={'gs':'Gold Skulltula','hp':'Piece of Heart','boss':'Boss Heart Container','bottle':'Bottle'}
        return f"{names.get(o['type'],o['type'])} #{o['collectionNumber']} of {o['collectionTotal']} - " if o.get('collectionTotal') else ''
    def card(o):
        return (f"- [ ] **{collectible_label(o)}{o['id']} — {o['name']}** ({o.get('region','')}; {o.get('age','')}; {o.get('time','')})\n"
            f"  - Where: {o.get('region','')} - {o.get('sublocation',o['name'])}.\n"
            f"  - Requires: {', '.join(o.get('requires',[])) or 'No additional item'}. {o.get('instructions','')}\n"
            + (f"  - Verification note: {o['note']}\n" if o.get('note') else '')
            + f"  - [Route {o['section']}](walkthrough.md#{o['section']}). {citations(o.get('sources',[]))}\n")
    full=['# The Hero’s Ledger — Switch 2 remake\n',f"Research: {g['meta']['researchDate']} · Game version: {g['meta']['gameVersion']}\n"]
    full+=['## Completion standard\n']+[p+'\n' for p in g['meta']['standard']]
    compact=['# Compact playthrough checklist\n','Full directions and evidence are in [walkthrough.md](walkthrough.md).\n']
    master=['# Master collectible checklist\n','Original stable IDs are retained across route changes.\n']
    warnings=['# Missables, final cleanup and postgame\n']+[f'- {w}\n' for w in g['meta']['warnings']]
    for s in g['sections']:
        ep=next(e for e in g['episodes'] if s['id'] in e['sections'])
        if s['id']==ep['sections'][0]:
            full.append(f"# Episode {ep['number']:02}: {ep['title']}\n")
            compact.append(f"# Episode {ep['number']:02}: {ep['title']}\n")
        os=[o for o in g['objectives'] if o['section']==s['id']]
        full+=[f"<a id=\"{s['id']}\"></a>\n\n## {s['number']:02}. {s['title']}\n",f"Start: {s.get('region','')} · {s.get('age','')} · {s.get('time','')}\n",f"Prerequisites: {', '.join(s.get('requires',[])) or 'See directions below'}.\n"]
        full += [f"> **Before proceeding:** {w}\n" for w in s.get('warnings',[])]
        full += [f'{i}. {step}\n' for i,step in enumerate(s.get('steps',[]),1)]
        full += [f"### {d['title']}\n\n{d['text']}\n" for d in s.get('details',[])]
        full+=['### Visit checklist\n']+[card(o) for o in os]
        e=s['expected'];totals=f"Expected: {e['gs']}/100 Skulltulas · {e['hp']}/36 heart pieces · {e['boss']}/8 boss containers · {e['hearts']} hearts."
        full += [totals+'\n',f"Next: {s['next']}\n",citations(s.get('sources',s.get('sourceIds',[])))+'\n']
        compact += [f"## {s['number']:02}. {s['title']}\n"]+[f"- [ ] {o['id']} — {o['name']}\n" for o in os]+[totals+'\n']
        if s.get('warnings'): warnings += [f"## {s['number']:02}. {s['title']}\n"]+[f'- {w}\n' for w in s['warnings']]
        if s['id'] in ('r35','r40','r41'):
            warnings += [f"## {s['title']} — audit\n"]+[card(o) for o in os]
    for typ,label in [('gs','Gold Skulltulas'),('hp','Pieces of Heart'),('boss','Boss Heart Containers'),('optional','Additional activities')]:
        master += [f'## {label}\n']+[card(o) for o in g['objectives'] if o['type']==typ]
    full+=['## Research limitations\n']+[f'- {x}\n' for x in g['meta'].get('limitations',[])]
    for name,parts in [('walkthrough.md',full),('playthrough-checklist.md',compact),('collectible-checklist.md',master),('missables-and-cleanup.md',warnings)]:
        (out/name).write_text('\n'.join(parts)+'\n',encoding='utf-8')
    episode_lines=['# The 25-episode playthrough\n','Episodes preserve the existing chronological route and all stable objective IDs. Length varies with dungeon and minigame retries.\n']
    for ep in g['episodes']:
        episode_lines.append(f"## Episode {ep['number']:02}: {ep['title']}\n")
        for sid in ep['sections']:
            s=next(x for x in g['sections'] if x['id']==sid)
            episode_lines.append(f"### [{s['title']}](walkthrough.md#{sid})\n")
            episode_lines.extend(f'{i}. {step}\n' for i,step in enumerate(s['steps'],1))
            episode_lines.extend(card(o) for o in g['objectives'] if o['section']==sid)
        e=ep['expected']
        episode_lines.append(f"Expected finish: {e['gs']}/100 tokens, {e['hp']}/36 heart pieces, {e['boss']}/8 boss containers, {e['hearts']} hearts.\n")
    (out/'episodes.md').write_text('\n'.join(episode_lines),encoding='utf-8')
    h=html.escape
    printable=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Print walkthrough — The Hero’s Ledger</title><style>body{font:16px/1.6 system-ui;max-width:900px;margin:2rem auto;padding:1rem;color:#162e24}h1,h2{line-height:1.2}h2{border-bottom:2px solid #b99238;padding-bottom:.6rem}h3{margin-bottom:.2rem}a{color:#285c42}li{margin-bottom:.5rem}.warning{border-left:4px solid #b99238;padding:.5rem 1rem}section{margin-bottom:3rem}@media print{.tools{display:none}section{break-before:page}h2,h3{break-after:avoid}a{color:inherit}body{max-width:none;margin:0;padding:0;font-size:11pt}}</style><body><div class="tools"><a href="./index.html#route">Back to companion</a> · Use your browser’s Print command</div><h1>The Hero’s Ledger</h1><p>Complete published route · Switch 2 remake · Research '+h(g['meta']['researchDate'])+' · Target '+h(g['meta']['gameVersion'])+'</p>']
    printable += ['<p>'+h(x)+'</p>' for x in g['meta'].get('limitations',[])]
    for s in g['sections']:
        ep=next(e for e in g['episodes'] if s['id'] in e['sections'])
        if s['id']==ep['sections'][0]:
            printable.append('<h2>Episode '+str(ep['number'])+': '+h(ep['title'])+'</h2>')
        printable += ['<section id="'+h(s['id'])+'"><h2>'+str(s['number'])+'. '+h(s['title'])+'</h2><p>'+h(s['region']+' · '+s['age']+' · '+s['time'])+'</p>']
        printable += ['<p class="warning"><b>Before proceeding: </b>'+h(w)+'</p>' for w in s.get('warnings',[])]
        printable += ['<ol>']+['<li>'+h(x)+'</li>' for x in s.get('steps',[])]+['</ol>']
        printable += ['<h3>'+h(d['title'])+'</h3><p>'+h(d['text'])+'</p>' for d in s.get('details',[])]
        printable += ['<h3>Visit checklist</h3><ul>']
        for o in g['objectives']:
            if o['section']!=s['id']: continue
            printable += ['<li>☐ <b>'+h(collectible_label(o)+o['id']+' — '+o['name'])+'</b> ('+h(o.get('age','')+'; '+o.get('time',''))+'): '+h(o.get('instructions',''))+'<br>Requires: '+h(', '.join(o.get('requires',[])) or 'No additional item')+(('<br><b>Verification note:</b> '+h(o['note'])) if o.get('note') else '')+'</li>']
        e=s['expected']
        printable += ['</ul><p>Expected: '+str(e['gs'])+' tokens · '+str(e['hp'])+' heart pieces · '+str(e['boss'])+' boss containers · '+str(e['hearts'])+' hearts.</p><p>Next: '+h(s['next'])+'</p>']
        linked=set(s.get('sources',[]))|{ref for o in g['objectives'] if o['section']==s['id'] for ref in o.get('sources',[])}
        printable += ['<p>Sources: '+' · '.join('<a href="'+h(refs[ref]['url'])+'">'+h(refs[ref]['title'])+'</a>' for ref in sorted(linked) if ref in refs)+'</p></section>']
    printable += ['</body></html>']
    (ROOT/'site'/'print.html').write_text('\n'.join(printable),encoding='utf-8')

if __name__=='__main__': build()
