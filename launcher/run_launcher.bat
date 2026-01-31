@echo off
echo Activating conda environment and launching BeamNG Accessible Launcher...
call conda activate bng
python "%~dp0accessible_launcher.py"
pause
