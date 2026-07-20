# deploy workflow — remaining setup

## 1. Vercel Git integration (auto preview on push)

1. Go to https://vercel.com/augmentedmike-7760s-projects/combis/settings
2. Connect GitHub repo `augmentedmike/mitehuacan.mx`
3. Set production branch = `main`
4. Set output directory = `site/combis`
5. Now every push to any branch gets an auto-preview URL
6. Promotion to production: Vercel dashboard → promote a preview deployment manually (or merge to main if Git integration is set to auto-deploy main)

## 2. Clean up duplicate Vercel projects

The manual `vercel deploy` created two projects:

| project | url | status |
|---|---|---|
| `mitehuacan` | mitehuacan.vercel.app | weird — serves vercel.com homepage, not our site |
| `combis` | combis-iota.vercel.app | ✅ working preview |

Delete the `mitehuacan` project from the Vercel dashboard. The `combis` project is the real frontend.

## 3. Test PWA on phone

- Open https://combis-iota.vercel.app on Android
- Confirm "Instalar" bar appears at bottom
- Tap it → native install dialog → app on home screen
- Open from home screen → standalone mode
- On iPhone: Share → Add to Home Screen (iOS doesn't prompt automatically)
