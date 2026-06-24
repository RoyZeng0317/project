@echo off
cd /d "C:\Users\Roy\Documents\GitHub\project"
git branch --unset-upstream
git add .
git commit -m "Auto-commit: nightly check 2026-06-25"
echo Done!
pause