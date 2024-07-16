"""This module creates a Design-AsBuilt comparison file containing
all the differences between the two files as a CSV."""
import os
from pathlib import Path
import logging
import tempfile
import argparse
import pandas as pd

#file1="DESIGN_Version4.xlsx"
#file2="ASBUILT_Version5.xlsx"

#AAArgument = file1+"|"+file2+"|"+"False"

logger=logging.getLogger(__name__)

logging.basicConfig(filename=tempfile.gettempdir()+'\as_built_differences.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger.info("Initiating...")

def plus_prefix(a):
    """If the number is negative this method 
    appends a negative sign to the string."""
    if a > 0:
        b = '+' + str(a)
    else:
        b = str(a)
    return b

def convert_xlsx_to_csv(file):
    """Converts xlsx files given as input 
    and returns a csv file path after converting."""
    csv_file_name = str(file.parent.resolve())+"\\"+str(file.stem)+".csv"
    data = pd.read_excel(file,engine="openpyxl")
    data.to_csv (csv_file_name,
                    index = None,
                    header = True)
    logger.info("Created File: %s",csv_file_name)
    return csv_file_name

def as_built_differences(file1,file2,keep_intermediate_files=False):
    """Given two files and the boolean, finds all rows not present 
    in both sheets. Then gives a negative value to rows present in the
    the first but not the second, and positive to the opposite."""
    try:
        logger.info("Detected Arguments: %s, %s, %s",
                    str(file1),str(file2),str(keep_intermediate_files))
        logger.info(file1)
        intermediate_file = str(file1.parent.resolve())+"\\"+"RowDifferences.csv"
        final_file = str(file1.parent.resolve())+"\\"+"Design-as_built_differences.csv"
        # Read and store content of an excel file

        converted_file1 = convert_xlsx_to_csv(file1)
        converted_file2 = convert_xlsx_to_csv(file2)

        with open(converted_file1, 'r',
                   encoding="UTF-8") as t1, open(converted_file2, 'r', encoding="UTF-8") as t2:
            text1 = t1.readlines()
            text2 = t2.readlines()
            #gather headers by resetting position in file.
            t1.seek(0)
            headers=t1.readline().replace("\n","")
            logger.info("Detected headers: %s", headers)
            header_list=list(headers.split(","))
            header_list.remove('Quantity')
            logger.info(header_list)

        with open(intermediate_file, 'w', encoding="UTF-8") as out_file:
            #write the headers row
            out_file.write("A/R,"+headers+"\n")
            #add all lines that were added in the asbuilt
            for line in text2:
                if line not in text1:
                    out_file.write("ADDITION,"+line)
            #add all lines that were removed from the asbuilt
            for line in text1:
                if line not in text2:
                    out_file.write("REMOVAL,"+line)

        df = pd.read_csv(intermediate_file)
        df_copy = df.copy()
        #multiply any columns that were removed between the first and second sheet
        #by -1 to show that the values were removed from the asbuilt
        df_copy.loc[df['A/R'] == 'REMOVAL', 'Quantity'] *= -1
        df_copy.drop(columns=df.columns[0], axis=1, inplace=True)
        #sum all quantities where headers in headers list match and group by rows
        df_copy = df_copy.groupby(header_list)['Quantity'].sum().reset_index()
        #add a plus to any positive quantity
        df_copy['Quantity'] = df_copy['Quantity'].apply(plus_prefix)
        #make a new file with the results
        df_copy.to_csv(final_file, index = None, header=True)
        if not isinstance(keep_intermediate_files,bool):
            logger.info("keep_intermediate_files is a string. Lowering case: %s",
                        keep_intermediate_files.lower())
            if keep_intermediate_files.lower() in ['false','no', '\'false\'', '\'no\'']:
                logger.info("keep_intermediate_files is false. Deleting files...")
                os.remove(converted_file1)
                os.remove(converted_file2)
                os.remove(intermediate_file)
        else:
            logger.info("keep_intermediate_files is a boolean")
            if not keep_intermediate_files:
                logger.info("keep_intermediate_files is false. Deleting files...")
                os.remove(converted_file1)
                os.remove(converted_file2)
                os.remove(intermediate_file)

        logger.info("Success")
        return final_file
    except Exception:
        logging.error("Exception occurred", exc_info=True)

def main():
    """Takes care of booting the program and parses input giving end-user documentation"""
    # parse arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("function",
                        help="Returns the differences between an AsBuilt and a Design from Maximo")
    parser.add_argument("file1", type=Path, help="The Design CSV file")
    parser.add_argument("file2", type=Path, help="The AsBuilt CSV file")
    parser.add_argument("bool", nargs='?', type=ascii,
                        help='Whether to keep files used to create final file')
    parsed_args = parser.parse_args()

    # try to get the function from the operator module
    try:
        func = globals()[parsed_args.function]
    except AttributeError:
        raise AttributeError(f"The function {parsed_args.function} is not defined.")

    # try to safely eval the arguments
    #try:
    #    eval1 = ast.literal_eval(parsed_args.file1)
    #    eval2 = ast.literal_eval(parsed_args.file1)
    #    eval3 = ast.literal_eval(parsed_args.bool)
    #    logger.info(eval1,eval2,eval3)
    #except SyntaxError as error:
    #    logger.info(error)
    #    raise SyntaxError(f"The arguments to {parsed_args.function}"
    #                      f"were not properly formatted.")

    # run the function and pass in the args, print the output to stdout
    kwargs = dict(file1=parsed_args.file1,file2=parsed_args.file2,
                  keep_intermediate_files=parsed_args.bool)
    logger.info(func(**{k: v for k, v in kwargs.items() if v is not None}))


if __name__ == "__main__":
    main()
