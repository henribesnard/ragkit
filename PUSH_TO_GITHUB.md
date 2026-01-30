# Push to GitHub

This project is ready to push to GitHub.

## 1. Add remote

```bash
git remote add origin https://github.com/henribesnard/ragkit.git
```

If the remote already exists:

```bash
git remote set-url origin https://github.com/henribesnard/ragkit.git
```

## 2. Push main branch and tags

```bash
git branch -M main
git push -u origin main
git push --tags
```

## 3. (Optional) Verify

```bash
git remote -v
git status -sb
```
