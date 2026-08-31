# 🚀 Deployment instructions

You said "Option B" (GitHub Actions deploy). Here's what to do.

## Step 1: Create an empty GitHub repo

Go to https://github.com/new and create a new **empty** repo.

- Name: `uzi-network` (or whatever you want)
- **Do NOT** initialize with README, .gitignore, or license — those exist locally
- Private is fine; public if you want the world to see your build process
- Click "Create repository"

## Step 2: Push the code from YOUR machine

You need the code on **your** machine, not on this VM. Either:

### Option 2a: Clone the VM to your laptop

```bash
# On your laptop:
scp -r ubuntu@<vm-host>:~/projects/uzi-network ./uzi-network
cd uzi-network
git remote remove origin   # in case scp preserved .git, just to be safe
git remote add origin git@github.com:YOUR_USERNAME/uzi-network.git
git push -u origin main
```

### Option 2b: Create a tarball, transfer, unpack

On **this VM**:

```bash
# (you'll need to ask me to do this, OR do it via the shell I have access to)
tar --exclude='.git' --exclude='node_modules' --exclude='dist' -czf uzi-network.tar.gz -C ~/projects .
```

Then on your laptop, `scp` the tarball, untar, and `git init` fresh.

### Option 2c (simplest): I generate a tarball now, you download it

I create `/tmp/uzi-network.tar.gz` and tell you the path so you can pull it however you normally move files off this VM.

---

## Step 3: Add GitHub repo secrets

In your new GitHub repo → **Settings → Secrets and variables → Actions**, add:

| Secret name | Where to get it |
|---|---|
| `CLOUDFLARE_API_TOKEN` | Cloudflare dashboard → My Profile → API Tokens → Create Token → "Edit Cloudflare Pages" template. Scope: Account → your account, Permissions: Pages:Edit |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare dashboard → Workers & Pages → right sidebar, "Account ID" |

You can also add the email provider secrets (see `.env.example`) — but the site will work without them (the signup form will just log to console in dev mode and return success).

---

## Step 4: Push triggers deploy

The moment `git push` reaches GitHub, the workflow at `.github/workflows/deploy.yml` runs:

1. `npm ci` (installs deps from lockfile)
2. `npx astro sync` (generates content types)
3. `npm run build` (builds to `dist/`)
4. Publishes `dist/` to Cloudflare Pages

First deploy takes 2-3 minutes. Watch it at:
- GitHub: repo → Actions tab
- Cloudflare: dashboard → Workers & Pages → uzi-network → Deployments

Once deployed, Cloudflare gives you a `*.uzi-network.pages.dev` URL automatically.

---

## Step 5: Attach uzi.network.store

In Cloudflare dashboard:
1. Workers & Pages → uzi-network → Custom domains
2. Click "Set up a custom domain"
3. Enter `uzi.network.store`
4. Cloudflare auto-configures DNS (since the domain is already on Cloudflare per your brief)

DNS propagation is instant since both ends are on the same Cloudflare account.

---

## What I can do right now to help

- Generate a tarball: `/tmp/uzi-network.tar.gz`
- Walk through any step in detail
- Update the workflow if you want a different build command or output dir

What would you like?