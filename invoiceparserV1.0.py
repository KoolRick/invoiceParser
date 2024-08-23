#!/usr/bin/env python
# coding: utf-8

"""
pip install pdfplumber
pip install tqdm
"""


#--------------------------------------------------
# run python invoiceparserV1.0.py invoice.pdf
#--------------------------------------------------

# In[1]:


# Libraries needed
import re
import sys
import os

import requests
import pdfplumber                           # Lib used for reading PDF
from tqdm import tqdm                       # Lib used for the progress bar shown while parsing the pdf


# In[2]:


# Invoice location path
# 2nd arg invoice pdf -> sys.argv[1]

# Checking number of args are correct
if(len(sys.argv) !=2):
    print("Error: Args number have to be 2")
    exit()
    
invoice=str(sys.argv[1])

pwd=os.path.abspath ('.')
invoicePath=pwd + "\\" +invoice

# Database name
bbdd = "`data_base_AWS-SPP_Discounts`"

# Dict used for months
monthOfYear = { # Dictionary for months
    'January': 1,
    'February': 2,
    'March': 3,
    'April': 4,
    'May': 5,
    'June': 6,
    'July': 7,
    'August': 8,
    'September': 9,
    'October': 10,
    'November': 11,
    'December': 12
}


# In[3]:

# This method finds the id and name of the client
def nameAndCode(page):

    # This method has one input parameter one pdf page and it will be reading line by line
    # until it finds the keywords of the page where are all the client details. When it 
    # finds the line where thess details are, it parse the ID and name of the client.
    
    # The next two lines are keypoints to find the line where the ID and name are
    # the 1st one(lineSummary) will find the page and the 2nd one will find the line.
    lineSummary = 'Summary for Linked Account'  # Keyword to look up tittle line.
    lineClient = re.compile(r'.*\d{12}')        # Regex pattern to look up for the 12 digit(ID), in which is the line where also the name is 

    for line in page.split('\n'):               # Loop for looking up the page
        if lineSummary in line:                 # if it finds the keyword "lineSummary"
            for line2 in page.split('\n'):      # Loop for looking up the line
                if lineClient.match(line2):     # if it finds the keypoint of the client
                    nameClientRaw, *vend = line2.split()
                    # This split will save whole line with the following:
                        # nameClientRaw= Client name(FIRST WORD ONLY!!!)
                        # vend = Remainder of the line
                            # [-1]=price
                            # [-2]=*literal "USD"
                            # [-3]=ID client
                            # ... the next [-i] will be the rest of the name of client
                    codClient=vend[-3]
                    codClient = codClient.replace("(","").replace(")","") # Cleans the ID deleting the parentheses in the ID
                    # Extract the not used data
                    vend.pop()#price
                    vend.pop()#*literal "USD"
                    vend.pop()#codClient
                    if vend!=[]: # Keeps loading the rest of the client's name
                        nameComplete = nameClientRaw + " " +' '.join(vend)
                    else:
                        nameComplete = nameClientRaw
                        
                    return codClient, nameComplete
    
## End method nameAndCode
# In[4]:

# This method find the current currency exchange during the period of the invoice.
def currencyExchange(page):

    # This method has one input parameter one pdf page and it will be reading line by line
    # until it finds the keywords of the page where exchange currency of the period of the invoice. 
    # When it  finds the line where this detail is, it extracts the exchange.

    lineCurrency = 'AWS Service Charges'# Keyword to find the exchange currency's line.
    
    for line in page.split('\n'):               # Loop for looking up the line
        if lineCurrency in line:                # if it finds the keyword "lineCurrency"
            title, *exchangeRaw = line.split()
            # This split will save whole line with the following:
                # title=*literal "AWS"
                # exchangeRaw= Remainder of the line
                    # [-1]=price in USD
                    # [-2]=*literal "USD"
                    # [-3]=price in EUR
                    # ...                   
                    # [-6]=exchange currency            
            currentExchange=exchangeRaw[-6]
            return currentExchange

## End method currencyExchange            
# In[5]:

# This method find the date of the period of the invoice.
def invoiceDate(page):

    # This method has one input parameter one pdf page and it will be reading line by line
    # until it finds the keywords of the page where date period of the invoice. 
    # When it  finds the line where this detail is, it extracts the year and month period in
    # letter in which it uses a dictionary to parse to numbers. Noticing the invoice are from past
    # month period.

    lineInvoiceBillingPeriod = 'This VAT Invoice is for the billing period'# Keyword to look up the line where date period is.
    
    for line in page.split('\n'):               # Loop for looking up the line
        if lineInvoiceBillingPeriod in line:
            title, *invoiceDateRaw = line.split()
           # This split will save whole line with the following:
                # title= *literal "VAT"
                # invoiceDateRaw=rest of the line
                    # [-1]=year
                    # [-2]=day(,)
                    # [-3]=month(in letters)           
            monthInvoice=invoiceDateRaw[-3]     # Save month
            yearInvoice=invoiceDateRaw[-1]      # Save year

            return (monthInvoice, yearInvoice)

## End method invoiceDate               
# In[6]:

# This method find the invoice ID number.
def invoiceId(page):

    # This method has one input parameter one pdf page and it will be reading line by line
    # until it finds the keywords of the page where invoice ID number. 
    # When it  finds the line where this detail is, it extracts the invoice number.

    lineInvoiceNumber = 'VAT Invoice Number:' # Keyword to look up in the PDF
    
    
    for line in page.split('\n'): # Search loop
        if lineInvoiceNumber in line:
            title, *invoiceIdRaw = line.split()
            # This split will save whole line with the following:
                # title = *literal "VAT"
                # invoiceIdRaw = rest of the line
                    # [-1]=invoice id              
            invoiceNumber=invoiceIdRaw[-1]
            return invoiceNumber

## End method invoiceId               
# In[7]:

# This method find services with credits SPP and its amount

## The main reason of creating this script is to collect all the "SPP discount" AWS give per each service.
## So this method will look for the keywords "Discount (AWS SPP Discount)" and extract the amount of discount.
## The PDF has a summary SPP discount per client and detailed SPP discount per service of each client.
## This amount summary per client can be used as a way to check if everything is going correctly

def serviceAndCredits(pdf, i, totalpages, p):

    # This has a input parameters the complete "pdf", the page "i" where it current is working on, the "totalpages"
    # of the pdf and an iterator "p", in which will be used for the progress bar to give feedback of the progress
    # during execution.
    # It will be reading all the pages, line by line. It will collecting the amount of services with credits SPP per
    # client.
  
    servCreditSPP = {}  # Dictionary to save all the SPP credits per service {service:credits}

    servicesXPag=[]     # Save ALL AWS services from the current/active page
    servicesXClient=[]  # Save ALL AWS services per client
    
    allCredits=[]       # Save all de amount USD credits
        
    # Keywords to look up in the PDF
    lineSummary = 'Summary for Linked Account'
    lineDetail = 'Detail for Linked Account'
    lineSPPCredit = 'Discount (AWS SPP Discount)'
    activeClient = True
    found = False
    
    while True:
        # Case base if there is no active client. Meaning, the client has no more credits SPP.
        if activeClient == False:
            break
        # Point to current page
        page = pdf.pages[i]
        text = page.extract_text()

        # As the lib PdfPumpler has the ability to filter data thru the font type. The next line is lambda function
        # filter extracting the data that in bold. In which, this will be all the services of a client in "page".
        clean_text = page.filter(lambda obj: obj["object_type"] == "char" and  "Bold" in obj["fontname"])
        textServ = clean_text.extract_text()
        
     
        #===================== Collecting ALL the services of current client ============================
        for line in textServ.split('\n'):               # The summary page of the current client
            if lineSummary not in line and lineDetail not in line and line != "":
                serv, *servRaw = line.split()
                servRaw.pop()#price
                servRaw.pop()#*literal USD
                if servRaw!=[]:
                    nameComplete = serv + " " +' '.join(servRaw)
                else:
                    nameComplete = serv           
                servicesXPag.append(nameComplete)            
            
        # ================== Collecting all discount SPP per client ===================  
        
        # Cloning list to iterate over one and modify the other
        loopingServices=servicesXPag[:]
    
        iterservices = iter(loopingServices)
        activeService = next(iterservices,"End")
        activeServiceNext = next(iterservices,"End")

        iterLine=iter(text.split('\n'))
        iterLineNext=iter(text.split('\n'))
        next(iterLineNext)
        for line in iterLine:          
            next(iterLineNext, -1)
            if lineDetail in line:
                if lineSPPCredit in line:
                    disc, *costSPPRaw = line.split()
                    costSPPRaw[-1] = costSPPRaw[-1].replace(",","")
                    allCredits.append("-" + costSPPRaw[-1])
            elif activeClient == True:
                while line != -1:
                    if activeServiceNext not in line:# or activeServiceNext!="End":
                        if lineSPPCredit in line:
                            disc, *costSPPRaw = line.split()
                            costSPPRaw[-1] = costSPPRaw[-1].replace(",","")
                            allCredits.append("-" + costSPPRaw[-1])
                            # This next line it is an issue with the encoding with this char. It needs to be handled.
                            servicesXClient.append(activeService.replace("ﬁ","fi"))
                            found = True
                            activeService = activeServiceNext
                            activeServiceNext = next(iterservices,"End")
                    elif activeServiceNext in line:
                        if found == False:
                             # This next line it is an issue with the encoding with this char. It needs to be handled.
                            servicesXClient.append(activeService.replace("ﬁ","fi"))
                            allCredits.append("0")

                        activeService = activeServiceNext
                        activeServiceNext = next(iterservices,"End")

                    found = False
                    line = next(iterLine,-1)
                if activeClient == True and found == False and activeService!="End":
                    servicesXClient.append(activeService)
                    allCredits.append("0")

        # For empty pages. Just showing "vat" ot "charge"            
        if servicesXPag == [] and allCredits == []:
            return {}, i
                      
        # This "totalCollected" will be used to verify the total collected at the end with the total shown in invoice.
        allCredits = list(map(float, allCredits))                 #cast to float
        totalCollected=round(sum(allCredits) - allCredits[0],2)   #round two decimals
        
        # Finishing client
        if i<totalpages-1:
            pageSig = pdf.pages[i+1]
            text2 = pageSig.extract_text()
            iterActiveClient=iter(text2.split('\n'))
            line2=next(iterActiveClient)
            # if client finished. The knows when a client is finish when on the first line of the next page says
            # "Summary for Linked Account"
            if lineSummary in line2:
                # Verifying total collected with total shown in invoice. Remember the first item of the list 
                # servicesXClient[0] is the total shown in the invoice.
                if totalCollected != allCredits[0]:
                    print(f"\nWarning: Total credits incorrect, please check the client on page: {i}")              
                activeClient = False
            else:
                activeClient = True 
                i=i+1
                p=next(iterProgress,-1)
        else:
            break
                

        # If there is an active service between two pages(named in one page but credits amount on next page)
        if allCredits[-1] != 0:
            servicesXPag=[]
        else:
            lastService=servicesXPag[-1]
            servicesXPag=[]
            servicesXPag.append(lastService)

    servicesXClient.pop(0)                      # Delete name client
    allCredits.pop(0)                           # Delete total
    servCreditSPP=dict(zip(servicesXClient, allCredits))  
 
    return servCreditSPP, i, p

# In[ ]:


if os.path.exists(invoicePath):
    print(f"Analyzing file {invoicePath}")
    with pdfplumber.open(invoicePath) as pdf:
        totalpages = len(pdf.pages)

        # Looking for currency exchange
        page = pdf.pages[0] # Because It is always on the first page.
        textPage = page.extract_text()
        currentExchange=currencyExchange(textPage)
        #print(currentExchange)

        # Looking for invoice ID number
        invoiceNumber=invoiceId(textPage)

        # Looking for date period invoice
        (monthInvoiceSQLfile, yearInvoice)=invoiceDate(textPage)

        lineFirstSummary="Summary for Linked Account"

        # getting the month
        if monthInvoiceSQLfile in monthOfYear:     # Maps the month in number
            monthInvoiceNum = monthOfYear[monthInvoiceSQLfile]

        # name of the file SQL that will be generated.
        name_file_generated = f'{monthInvoiceSQLfile}-{yearInvoice}SPP.sql'

        with open(f'{name_file_generated}', 'w', encoding="utf-8") as file:
            sql = f"INSERT INTO {bbdd} (Year, Month, linkedAccountId, LinkedAccountName, Service, Credits, InvoiceID, CurrencyExchange) VALUES "
            file.write(sql)

            #Progress Bar
            iterProgress=iter(tqdm (range (totalpages), desc="Loading..."))
            p=next(iterProgress,-1)
            while p != -1:
                i=0
                while i < totalpages:
                    page = pdf.pages[i]
                    clean_text = page.filter(lambda obj: obj["object_type"] == "char" and  "Bold" in obj["fontname"])
                    textServ = clean_text.extract_text()
                    iterLine=iter(textServ.split('\n'))
                    line = next(iterLine)
                    if lineFirstSummary not in line:
                        i=i+1                           # next page
                        p=next(iterProgress,-1)         # progress bar...
                    else:
                        break

                while i < totalpages:
                    page = pdf.pages[i]
                    textPage = page.extract_text()
                    
                    # Looking for ID client and name
                    codClient, nameComplete = nameAndCode(textPage)
                    sql = f"\n\n-- {nameComplete}"
                    file.write(sql)

                    # Looking for SPP discount per page/client
                    servCreditSPP, i, p = serviceAndCredits(pdf, i, totalpages, p)

                    #print(f"servCreditSPP: {servCreditSPP}")
                    
                    for services in servCreditSPP:     # Iterating clients

                        if(i==totalpages-1 and services == list(servCreditSPP.keys())[-1]):#ultimo
                            sql=f"\n({yearInvoice}, {monthInvoiceNum}, \"{codClient}\", \"{nameComplete}\", \"{services}\", {servCreditSPP[services]}, \"{invoiceNumber}\", {currentExchange})"
                        else:
                            sql=f"\n({yearInvoice}, {monthInvoiceNum}, \"{codClient}\", \"{nameComplete}\", \"{services}\", {servCreditSPP[services]}, \"{invoiceNumber}\", {currentExchange}),"
                        file.write(sql)    
                    i=i+1                               # next page
                    p=next(iterProgress,-1)             # progress bar...

        print(f'File SQL generated --> "{name_file_generated}"')
        print("Done!")
else:
    print("File not found!")
    exit()

