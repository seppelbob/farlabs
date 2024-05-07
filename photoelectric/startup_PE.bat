:loop
taskkill /F /IM python.exe
taskkill /F /IM ffmpeg.exe
ping 127.0.0.1 -n 5

python identify_cameras.py

start c:/farlabs/python/python.exe streamer_2.0.py
start c:/farlabs/python/python.exe photo2.py

:innerloop
timeout /t 60 /nobreak

time /t > tmpFile 
set /p timenow= < tmpFile 
del tmpFile 


::if /i %timenow:~3,2% == 00 (goto :loop)
for /f %%a in ('time /t') do set timenow=%%a


goto :innerloop


