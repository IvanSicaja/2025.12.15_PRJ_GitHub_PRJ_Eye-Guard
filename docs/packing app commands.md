1. Install PyInstaller
pip install pyinstaller
2. Navigate to the folder where your main.py file is located:
cd "C:\User..."
3. Create a standalone executable with icon
pyinstaller --clean --onefile --windowed --name EyeGuard --icon="assets/media/icons/shield_extrected.png" --distpath publish --workpath publish/build --add-data "assets/media/sounds/sound.mp3;assets/media/sounds" --add-data "assets/media/icons/shield_extrected.png;assets/media/icons" --add-data "assets/media/figures;assets/media/figures" main\main.py

4. Optional for removing non necessary files -> run in pycharm terminal
Get-ChildItem -Path .\publish -Recurse | Where-Object { $_.Extension -ne '.exe' } | Remove-Item -Force -Recurse

