# Saved-results deployment

Public URL: https://spotify-review-insights-three.vercel.app

The final published snapshot contains 100,000 classified reviews and 13 empty quarantines. The original full source was profiled separately. Anonymous HTTP access retrieves the final saved database without model calls.

The Vercel project is `spotify-review-insights`, ID `prj_tgL8KSoKMBQrwer2fmtHv2LbQm5d`, on the existing `knit3` Hobby team. The CLI was used because the connected MCP credential could not access that team. No paid hosting plan was purchased.

`deployment/app.py` exports Flask routes backed by the bundled read-only SQLite database. No API key or model runtime is deployed. `deployment/templates/index.html` renders the frontend. The database contains processed records, aggregate rankings and the generated memo; it is not an in-memory stand-in.

Update the published snapshot after the final run:

```sh
python3 dashboard.py --import-run runs/jev-500/resume --db deployment/dashboard.sqlite
cp web/dashboard.html deployment/templates/index.html
vercel deploy deployment --prod --yes --scope knit3
```

The Vercel link metadata is local and ignored. On another computer, link the deployment directory to the named project before deploying. The original Dockerfile remains an alternative container route.
