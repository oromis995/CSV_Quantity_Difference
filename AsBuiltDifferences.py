import os
import pandas as pd 
from pathlib import Path
import logging
import tempfile
import argparse
import ast

#file1="DESIGN_Version4.xlsx"
#file2="ASBUILT_Version5.xlsx"

#AAArgument = file1+"|"+file2+"|"+"False"

logger=logging.getLogger(__name__)

logging.basicConfig(filename=tempfile.gettempdir()+'\AsBuiltDifferences.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger.info("Initiating...")

def plus_prefix(a):
    if a > 0:
        b = '+' + str(a)
    else:
        b = str(a)
    return b

def convertXLSXtoCSV(file):
    
    csvFileName = str(file.parent.resolve())+"\\"+str(file.stem)+".csv"
    data = pd.read_excel(file,engine="openpyxl")
    data.to_csv (csvFileName,  
                    index = None, 
                    header = True)
    logger.info("Created File: "+csvFileName)
    return csvFileName

def asBuiltDifferences(file1,file2,keepIntermediateFiles=False):
    try:
        logger.info("Detected Arguments: "+str(file1)+", "+str(file2)+", "+str(keepIntermediateFiles))
        logger.info(file1)
        intermediateFile = str(file1.parent.resolve())+"\\"+"RowDifferences.csv"
        finalFile = str(file1.parent.resolve())+"\\"+"Design-AsBuiltDifferences.csv"
        # Read and store content of an excel file  
        
        convertedFile1 = convertXLSXtoCSV(file1)
        convertedFile2 = convertXLSXtoCSV(file2)
        
        with open(convertedFile1, 'r') as t1, open(convertedFile2, 'r') as t2:
            text1 = t1.readlines()
            text2 = t2.readlines()
            #gather headers by resetting position in file.
            t1.seek(0)
            headers=t1.readline().replace("\n","")
            logger.info("Detected headers: " + headers)
            headerList=list(headers.split(","))
            headerList.remove('Quantity')
            logger.info(headerList)

        with open(intermediateFile, 'w') as outFile:
            #write the headers row 
            outFile.write("A/R,"+headers+"\n")
            #add all lines that were added in the asbuilt
            for line in text2:
                if line not in text1:
                    outFile.write("ADDITION,"+line)
            #add all lines that were removed from the asbuilt
            for line in text1:
                if line not in text2:
                    outFile.write("REMOVAL,"+line)
        

        df = pd.read_csv(intermediateFile) 
        df_copy = df.copy()
        #multiply any columns that were removed between the first and second sheet
        #by -1 to show that the values were removed from the asbuilt
        df_copy.loc[df['A/R'] == 'REMOVAL', 'Quantity'] *= -1
        df_copy.drop(columns=df.columns[0], axis=1, inplace=True)
        #sum all quantities where headers in headers list match and group by rows
        df_copy = df_copy.groupby(headerList)['Quantity'].sum().reset_index()
        #add a plus to any positive quantity
        df_copy['Quantity'] = df_copy['Quantity'].apply(plus_prefix)
        #make a new file with the results
        df_copy.to_csv(finalFile, index = None, header=True)
        if not isinstance(keepIntermediateFiles,bool):
            logger.info("keepIntermediateFiles is a string. Lowering case: "+keepIntermediateFiles.lower())
            if keepIntermediateFiles.lower() in ['false','no', '\'false\'', '\'no\'']:
                logger.info("keepIntermediateFiles is false. Deleting files...")
                os.remove(convertedFile1)
                os.remove(convertedFile2)
                os.remove(intermediateFile)
        else:
            logger.info("keepIntermediateFiles is a boolean")
            if not keepIntermediateFiles:
                logger.info("keepIntermediateFiles is false. Deleting files...")
                os.remove(convertedFile1)
                os.remove(convertedFile2)
                os.remove(intermediateFile)

        logger.info("Success")
        return (finalFile)
    except Exception:
        logging.error("Exception occurred", exc_info=True)

def main():
    # parse arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("function", help="Returns the differences between an AsBuilt and a Design from Maximo")
    parser.add_argument("file1", type=Path, help="The Design CSV file")
    parser.add_argument("file2", type=Path, help="The AsBuilt CSV file")
    parser.add_argument("bool", nargs='?', type=ascii, help='Whether to keep files used to create final file')
    parsedArgs = parser.parse_args()

    # try to get the function from the operator module
    try:
        func = globals()[parsedArgs.function]
    except AttributeError:
        raise AttributeError(f"The function {parsedArgs.function} is not defined.")

    # try to safely eval the arguments
    #try:
    #    eval1 = ast.literal_eval(parsedArgs.file1)
    #    eval2 = ast.literal_eval(parsedArgs.file1)
    #    eval3 = ast.literal_eval(parsedArgs.bool)
    #    logger.info(eval1,eval2,eval3)
    #except SyntaxError as error:
    #    logger.info(error)
    #    raise SyntaxError(f"The arguments to {parsedArgs.function}"
    #                      f"were not properly formatted.")

    # run the function and pass in the args, print the output to stdout
    kwargs = dict(file1=parsedArgs.file1,file2=parsedArgs.file2,keepIntermediateFiles=parsedArgs.bool)
    logger.info(func(**{k: v for k, v in kwargs.items() if v is not None}))


if __name__ == "__main__":
    main()


        