# GitHub to Netlify

This project is static. The committed root `netlify.toml` sets the publish directory to `site`. There is **no build command**, dependency installation, framework, environment variable or secret to configure. All production files are committed in `site/`.

## Connect once

1. Create your own GitHub repository and push the project files, preserving `netlify.toml` at the repository root and `site/index.html` inside `site`.
2. Sign in to Netlify and choose your team. Choose **Add new project**, then **Import an existing project**.
3. Choose **GitHub**. Authorize Netlify to access the intended repository, then select it.
4. Select the production branch you pushed (commonly `main`). Keep the repository root as the base directory. Confirm the publish directory is `site` and the build command is empty. The committed `netlify.toml` supplies the publish configuration; do not add an npm command.
5. Finish the import/deploy flow. When Netlify reports a successful deployment, open its URL. Test a route deep link and export/import your progress if moving from localhost.

No external account actions were performed in preparing this project. Push and publication remain your actions.

## Future updates

Edit the source JSON or interface locally, run the documented generator and validation, and commit the changed files including `site/data.js` and Markdown exports. Push to the connected branch. Netlify's normal continuous deployment publishes the committed `site` directory automatically.

## Troubleshooting

- **404 at the home page:** check that `site/index.html` exists on the deployed branch and the publish directory is exactly `site` relative to the repository root.
- **Assets missing:** preserve filenames and relative paths; confirm `app.js`, `styles.css`, and `data.js` were committed. No files outside `site` are loaded at runtime.
- **Netlify tries to build a framework:** clear any dashboard build command or base directory left from another project. This repository needs neither npm nor a build step.
- **Content edits not showing:** run `python scripts/generate.py`, commit the generated data file and push. Check the deployment's commit against GitHub.
- **Progress appears empty after deployment:** browser storage is isolated by site origin. Export JSON at the old address and import it at the new address. Changing browsers or clearing storage also requires an export backup.
- **Deep links:** routes use `#` fragments. No rewrite/fallback is needed; the server always loads `index.html`.

Interface wording and configuration behavior checked November 23, 2026 against [Netlify: Add new project](https://docs.netlify.com/manage/projects/add-new-project/), [continuous deployment](https://docs.netlify.com/build/git-workflows/overview/), and [file-based configuration](https://docs.netlify.com/build/configure-builds/file-based-configuration/). Netlify may change labels after that date.
