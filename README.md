# The Rebels Garage website

Static site built with Python (no npm). `python3 src/build.py` builds into `dist/`; Vercel runs the same command.

- Pages and copy: `src/build.py` (services list in `SERVICES`, photo slots in `PHOTO`)
- Styles and scripts: `src/styles.css`, `src/site.js`
- Blog posts: `content/posts/*.html` with details as JSON at the top. A post dated in the future stays hidden until a build runs on or after that date (Pacific time).
- Photos: put masters in `media/` as `.webp`, then run the build locally with Pillow so the crops in `img/` get made, and commit both.
- Forms: `api/form.js` emails quotes through Resend. Needs `RESEND_API_KEY` in Vercel; optional `FORM_TO` and `FORM_FROM`.
