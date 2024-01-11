# ANPR-EXAMPLE
An ANPR system made by a Brazilian Python Apprentice, isn't polished (but I made some functional versions of it).

How it works:

The code tries to connect and authenticate the connection before it gathers information from the Intelbras NVD/DVR  (by their IP, Port, User and Password), which by itself control the cameras attached to it. After it establishes the connection and "grab" those visual information (by snapshots attached to a URL) the code starts doing his job, which is:
It traces a Region of Interest (ROI) using CascadeClassifier and PlateCascade, then this ROI will be saved (because the ROI now have the exact car plate area), after doing this, the image will be treated by some OpenCV2 commands, that will reduce the noise from the ROI and improve the useful character surface. 
When the treatment is done, PyTesseract tries to recognize patterns and similarities of those characters, then PyTesseract gather the results and gives it to the user or just save it in the code.
After the last step, 2 different things can happen: 

  1° If you're using v1.0 (without character filter), the code will just count similar characters, if 5 of 7 are the same, then send a signal to MQTT.

  2° If you're using v1.1 (non-tested, with character filter), the code will change characters that are in the wrong position, using a bad coded condition (which looks at the Brazilian car plate pattern) comparing the following (X for letter and N for number) "XXXNXNN".
      I'll be honest, when I say bad coded condition, the explanation is: in the past (October to December) my time was too short to study Python as it should be studied, so I tried my best to work only with what I had at the moment (my low and limited knowledge).

When the character similarity filter properly works and ends its cycle, the code will continue running as normal, which is, if the plate is inside the DataFrame (a CSV file or an Excel sheet) a signal will be sent to the MQTT Broker, which will be analyzed by the ESP lately (Signal is 0? Then do nothing, if signal is 1 set an GPIO HIGH).   
