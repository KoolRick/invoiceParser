# invoiceParser
This is a script for parsing PDF files getting data from specifics keywords.
Then it creates a SQL script to execute over a data base.


## Getting Started

This project was inspired to make easier the billing of the consumption of each month of cloud services, in this case AWS. 
It was needed to extract manually from the pdf invoices to account for some credits AWs gives.

So this script was created to eliminate this manual search avoding long efforts extracting this data, human error and saving time.

### Prerequisites

You will need the following libraries.


Python IDE, in my case I used "Visual Studio Code" with "Anaconda Comunity".
Python
    >*version used: 3.12.4*
pdfplumber  --> It is the protagonist for this project. It will handle the PDF file.
    >*version used: 0.11.2*
tqdm        --> It used for a graph a progress bar.
    >*version used: 4.66.4*

### Installing

First install Python.

Install the libraries dependencies. You can install through the Anaconda GUI these libraries.

```
pdfplumber
tqdm
```

Or from terminal with these commands.

```
pip install pdfplumber
pip install tqdm
```

## Running the tests

For testing, It will use an example of an invoice from AWS, added as "invoice.pdf" into the project. This script will read line by line on each page using keywords to extract credits needed.

### Here is an example of correct run.

![Correct example](https://github.com/KoolRick/invoiceParser/blob/main/readmeFiles/correctRun.jpg?raw=true)

This script have a data validator to check it has all the amounts correct.

### Here is an example of an incorrect run.

It is evaluated as a warning to save time. It will generate the file with a warning.

![Warning example](https://github.com/KoolRick/invoiceParser/blob/main/readmeFiles/warningRun.jpg?raw=true)

## Deployment

These are the domentation of the libraries used.

## Built With

* [pdfplumber](https://pypi.org/project/pdfplumber/) - The web pdf handler used
* [tqdm](https://tqdm.github.io/) - Library for the progress bar