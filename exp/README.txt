
How to create a new experiment. 

1. Copy an existing experiment to modify: cp -r old_exp new_exp
2. Delete untracked files from the new experiment directory: git clean -df new_exp
3. Check in the new experiment: git add new_exp ; git commit -a -m "Added experiment new_exp"
4. Do a similar thing for the experiment inputs: cd /short/v45/auscom/
5. cp -r old_exp new_exp
6. git annex add new_exp
7. git commit -a -m "Added new experiment data for new_exp"

