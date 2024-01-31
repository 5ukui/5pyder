
<div align="center">
  <a href="https://github.com/HuthaifaM/Spyder">
    <img src="Icons/appLogo.png" alt="Logo" width="180" height="180">
  </a>
  
  <h3 align="center">Spyder</h3>
</div>

## About The Project
Spyder is a Python-based Cryptocurrency forensics tool that visualizes transactions to allow analysts to trace cryptocurrency thats been distributed accross different wallet addresses.

<div align="center">
  <a href="https://github.com/HuthaifaM/Spyder">
    <img src="Icons/Application Screenshot.PNG" alt="Logo">
  </a>
</div>
The application utilizes Etherscan.io's API to retrieve a wallet address's transaction histroy and visualizes it in the form of a network graph. The wallet addresses are assigned different icons based on their category as shown below:

#### Parent
<div align="left">
  <a href="https://github.com/HuthaifaM/Spyder">
    <img src="Icons/parent.png" alt="Parent" height=80 width=80>
  </a>
</div>
This is the wallet address that the use initially searches for. The rest of the wallet addresses branching out of the parent node are categorized as child nodes and assigned a different color icon.

#### Child
<div align="left">
  <a href="https://github.com/HuthaifaM/Spyder">
    <img src="Icons/user.png" alt="Child" height=80 width=80>
  </a>
</div>
This icon is assigned to all the wallet addresses that branch out of the parent node.

#### Expanded Child
<div align="left">
  <a href="https://github.com/HuthaifaM/Spyder">
    <img src="Icons/userNodeExpand.png" alt="ExpandedChild" height=80 width=80>
  </a>
</div>
This icon is assigned to a child node that had been expanded by the user double clicking on it.

#### Cryptocurrency
<div align="left">
  <a href="https://github.com/HuthaifaM/Spyder">
    <img src="Icons/eth.png" alt="ExpandedChild" height=80 width=80>
  </a>
</div>
This icon represents the cryptocurrency that is being sent to and received by the different wallet addresses. This icon is accompanied by an arrow connecting the two nodes together that points in the direction of the receiving end, along with the amount of cryptocurrency being sent out/received.

## Libraries
Badges because they look cool:

![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-%23ffffff.svg?style=for-the-badge&logo=Matplotlib&logoColor=black)
![NumPy](https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white)

Additional libraries include:

Pyvis, PyQt5, PyQtWebEngine, requests, termcolor, slither-analyzer


## Instructions
Note: Always use a virtual environment when installing dependancies. :exclamation:

These API keys are required for this application to function:

• Ethplorer.io

• Etherscan.io

Once these API keys are obtained, append them to the creds.py file.

Install the dependencies:
```
pip install -r requirements
```
Execute the application:
```
python main.py
```
