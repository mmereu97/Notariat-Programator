REM Batch file to copy notarial_scheduler.db and launch Programator.exe

REM Check if source file exists
if not exist "Q:\Documente\- Filme\Programe Mereu Mihai\Programator\notarial_scheduler.db" (
    echo Error: Source file not found!
    pause
    exit /b 1
)

REM Copy with overwrite
echo Copying database file...
xcopy /Y "Q:\Documente\- Filme\Programe Mereu Mihai\Programator\notarial_scheduler.db" "D:\PycharmProjects\Notariat-Programator\"
xcopy /Y "Q:\Documente\- Filme\Programe Mereu Mihai\Programator\document_types.json" "D:\PycharmProjects\Notariat-Programator\"
xcopy /Y "Q:\Documente\- Filme\Programe Mereu Mihai\Programator\window_settings.json" "D:\PycharmProjects\Notariat-Programator\"


d:
cd\
cd PycharmProjects
cd Notariat-Programator
Programator.exe
