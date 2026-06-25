@echo off
cd /d "C:\Users\Roy\Documents\GitHub\project"
git rm --cached -r --force "BB Call Call back/BB Call/layout/BB Call/.history"
git rm --cached -r --force "Smart NFU School/Layout/.history"
git commit -m "Remove .history submodule entries"
git push
echo Done!
pause