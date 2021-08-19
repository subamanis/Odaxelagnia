# Odaxelagnia

[BiteFight](https://en.bitefight.gameforge.com/game) CLI browser automation tool, using selenium.

<b>Odaxelagnia</b>: A <ins>paraphilia</ins> in which biting or being bitten leads to sexual arousal.

<b>Paraphilia</b>: Sexual behavior that is considered deviant or abnormal.

## Details

The program opens a software-controlled browser window and performes the necessary actions in real time. 
The only supported browser is Google Chrome 92, due to inability to suppress log messages on others.

While the program is in the middle of performing an action, you should not click buttons or links that change the structure of the website on the tab that it is performing, because the program expects to find particular the webpage elements. The browser opened by the program can still be used normally by opening other tabs, and if the program is not performing an action, you can even use the bitefight tab manually. 

Keep in mind that for example if you start a shift in the graveyard or start a story, and before finishing you tell the program to perform another action, it will fail. 

### First execution 
When you run the program for the first time, it will ask for you account username and password so it can log in automatically. The account details are saved only locally in a .txt file inside src/files, so they are absolutely safe since the program is running only on your pc.
Also, after the account creation, the program will make you choose 4 out of the 8 aspects to focus on the tavern stories, and will save your preferances inside a .txt in the same folder as the account details.
Both files can be manually altered as long as they retain the same structure.

## Features

The program can automatically handle [<b>manhunts</b>](#ManHunt), <b>grotto fights</b>, <b>tavern stories</b>, <b>graveyard</b> and <b>healing</b> in the church, according to your input.

- <b>1) ManHunt</b>: You specify the target (Farm, Village, Small Town,...) and the number of hunts.
- <b>2) Grotto</b>: You specify the difficulty level and the number of fights.
- <b>3) Stories</b>: You specify how many stories you want to perform (1 story = 40 choices).
- <b>4) Graveyard</b>: You specify how many shifts you want in the graveyard (1 shift = 15 minutes). The program after 15 minutes will wake up to put you again in a new shift if the computer isn't in sleep mode.
- <b>5) Heal</b>: No input is required, the program heals in the church.

Or you can press 0 to exit the program.

## How to use
Make sure you have Python installed in your machine, and you have added it to PATH.

Before first execution run the file "init.bat" once (it may take some seconds). Then you can run the program every time by only running "run.bat"

Inside the src folder, there are is the chrome webdriver that corresponds to Chrome 92, if your browser version is not compatible with the existing webdriver, you can download the new webdriver that matches with your browser and replace it. 
