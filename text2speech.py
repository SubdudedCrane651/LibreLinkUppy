# Import the required module for text
# to speech conversion
import sys
sys.path.append('.venv/Lib/site-packages/')
#sys.path.append('/home/richard/.local/lib/python3.8/site-packages/')
from gtts import gTTS
from playsound import playsound
# This module is imported so that we can
# play the converted audio
import os
# The text that you want to convert to audio
count = 0
mytext= []
command=""
command2=""
file=""
deletefiles=False
language="en"

length = len(sys.argv)

try:

  command = sys.argv[1]

  if length > 3:
      command = sys.argv[1]
      command2 = sys.argv[2]
      if (command2 == "--in" or command.find("--lang")>-1):
        if command=="--lang=fr":
          language="fr"
          mytext.append(sys.argv[2])   
        if command=="--lang=en":
          language="en"
          mytext.append(sys.argv[2])
        if command2=="--in":
          file = sys.argv[3]
          with open(file,'r+') as File:
            mytext = File.readlines()
        else:       
            mytext.append(command)

  elif length==3:
    command = sys.argv[1]
    if (command == "--in" or command.find("--lang")>-1):
      if command=="--lang=fr":
        language="fr"
        mytext.append(sys.argv[2])   
      if command=="--lang=en":
        language="en"
        mytext.append(sys.argv[2])
      if command=="--in":
        file = sys.argv[2]
        with open(file,'r+') as File:
            mytext = File.readlines()
    else:       
        mytext.append(command)

  else:
    playsound(os.path.dirname(__file__)+r"/speak_0.mp3")
    sys.exit()

except:
   try:
    playsound(os.path.dirname(__file__)+r"/speak_0.mp3")
   except:
    sys.exit()


myobj = gTTS(text="mytext", lang=language, slow=False)   

#mytext = "Call from Clement Perreault at 450-655-4677"
# Language in which you want to convert


for text in mytext:
    # Passing the text and language to the engine,
    # here we have marked slow=False. Which tells
    # the module that the converted audio should
    # have a high speed
    if text != "":
    # Saving the converted audio in a mp3 file named
    # welcome
      print(text)
      myobj.text=text
      audio_file = os.path.dirname(__file__)+"/speak_"+str(count)+".mp3"
      # Delete the file if it exists
      if os.path.exists(audio_file):
         os.remove(audio_file)
      myobj.save(audio_file)
    # Playing the converted file
      playsound(audio_file)
      count=count+1
      if count==2:
        count=0
        os.remove("speak_"+str(count)+".mp3")
        os.remove("speak_"+str(count+1)+".mp3")
        deletefiles=True
if deletefiles:        
 myobj.save(audio_file)          
