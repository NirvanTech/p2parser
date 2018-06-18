#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
P2P platform Lendy.co.uk parser for Lendy_Statement_YYYYMMDD-YYYYMMDD.csv file and set of statistics functions
"""

import pandas as pd
import csv
from datetime import datetime
import argparse
import os

import utils

DATA_FOLDER = 'data/'

LENDY_CSV_FILE = 'lendy.csv'


def convertToStandardCSV(csvFilepath):

    if not os.path.exists(csvFilepath):
        print("File {} does NOT exists. END of script".format(csvFilepath))
        os._exit(1)

    sourceFile = csvFilepath
    destinationFile = os.path.dirname(os.path.realpath(__file__)) + '/' + DATA_FOLDER + LENDY_CSV_FILE
    try:
        print('Trying to convert', sourceFile, 'to', LENDY_CSV_FILE)
        df = pd.read_csv(sourceFile)

        print('File', sourceFile, 'loaded.')

        # reverse row order
        df = df[::-1]

        df.to_csv(destinationFile, header=[str(x) for x in range(len(df.columns))], encoding='utf-8', index=False)
        print('File', sourceFile, 'exported to', destinationFile)
    except Exception as e:
        print('Conversion failed.', e)


def getDataFromCSVfile(filepath):

    with open(filepath) as csvFile:
        reader = csv.DictReader(csvFile, delimiter=',')

        for row in reader:
            if not row['0']:
                continue
            if not row['5']:
                row['5'] = 0.0
            yield row


def getRowData(row):
    fee = None
    principalRepaid = None
    interestReceived = None
    chargesReceived = None
    cashFlowChange = None

    try:
        if row['1'] == 'Deposit':
            cashFlowChange = float(row['8'])

        # TODO withdrawal?
        # if row['1'] == 'Deposit':
        #     cashFlowChange = float(row['8'])

        if row['1'] == 'Interest':
            interestReceived = float(row['8'])

        if row['1'] == 'Bonus':
            chargesReceived = float(row['8'])

        if row['1'] == 'Capital Repayment' or row['1'] == 'Capital repayment':
            principalRepaid = float(row['8'])

        return {'rawDate': row['0'], 'fee': fee, 'principalRepaid': principalRepaid,
                'interestReceived': interestReceived, 'chargesReceived': chargesReceived, 'cashFlowChange': cashFlowChange}
    except Exception as e:
        print(e, row)


def getCashInGame(cashInGame, rowData):
    if rowData['cashFlowChange']:
        cashInGame = cashInGame + rowData['cashFlowChange']
    if rowData['interestReceived']:
        cashInGame = cashInGame + rowData['interestReceived']
    if rowData['chargesReceived']:
        cashInGame = cashInGame + rowData['chargesReceived']
    if rowData['fee']:
        cashInGame = cashInGame + rowData['fee']
    return cashInGame


def getFees():
    fees = 0.0

    for row in getDataFromCSVfile(DATA_FOLDER + LENDY_CSV_FILE):
        rowData = getRowData(row)
        if rowData['fee']:
            yield (rowData['fee'], rowData['rawDate'])
            fees = fees + rowData['fee']

    yield (round(fees, 2), 'Total fees paid')


def getTotals():
    principalRepaid = 0.0
    interestsReceived = 0.0
    charges = 0.0
    fees = 0.0
    cashInGame = 0.0

    for row in getDataFromCSVfile(DATA_FOLDER + LENDY_CSV_FILE):
        rowData = getRowData(row)
        cashInGame = getCashInGame(cashInGame, rowData)

        if rowData['principalRepaid']:
            principalRepaid = principalRepaid + rowData['principalRepaid']
        if rowData['interestReceived']:
            interestsReceived = interestsReceived + rowData['interestReceived']
        if rowData['chargesReceived']:
            charges = charges + rowData['chargesReceived']
        if rowData['fee']:
            fees = fees + rowData['fee']

    yield(round(cashInGame, 2), 'Cash in game')
    yield(round(interestsReceived, 2), 'Total interests received')
    yield(round(charges, 2), 'Total charges received')
    yield(round(fees, 2), 'Total fees paid')


def getPreviousMonth():
    cashInGame = 0.0

    feePaid = 0.0
    principalRepaid = 0.0
    interestsReceived = 0.0
    cashInGameForThisMonth = None

    if datetime.today().month - 1 > 0:
        previousMonth = datetime.today().month - 1, datetime.today().year
    else:
        previousMonth = 12, datetime.today().year - 1

    for row in getDataFromCSVfile(DATA_FOLDER + LENDY_CSV_FILE):
        rowData = getRowData(row)

        date = datetime.strptime(rowData['rawDate'], '%d/%m/%Y')

        if previousMonth == (date.month, date.year):
            if rowData['principalRepaid']:
                principalRepaid = principalRepaid + rowData['principalRepaid']
            if rowData['interestReceived']:
                interestsReceived = interestsReceived + rowData['interestReceived']
            if rowData['chargesReceived']:
                interestsReceived = interestsReceived + rowData['chargesReceived']
            if not cashInGameForThisMonth:
                cashInGameForThisMonth = cashInGame

        cashInGame = getCashInGame(cashInGame, rowData)
        if rowData['fee']:
            feePaid = rowData['fee']

    yield (round(cashInGameForThisMonth, 2), 'Cash in game for this month')
    yield (round(interestsReceived, 2), 'Total interests received')
    yield (round(feePaid, 2), 'Fee paid')
    yield (round(principalRepaid, 2), 'Total principal repaid')


def getTotalByMonth():
    principalRepaid = 0.0
    interestsReceived = 0.0
    cashInGame = 0.0

    previousMonthPrincipalRepaid = 0
    previousMonthInterestsReceived = 0
    previousMonthCashInGame = 0

    currentMonthDate = datetime.strptime('1.1.2000', '%d.%m.%Y')
    currentMonthCashInGame = 0

    newMonth = False

    roi = 0.0

    yield('Month', 'CiG', 'Inter.', 'Fee', 'ROI', 'Princip.')

    for row in getDataFromCSVfile(DATA_FOLDER + LENDY_CSV_FILE):
        rowData = getRowData(row)

        rowDate = datetime.strptime(rowData['rawDate'], '%d/%m/%Y')

        if rowDate.month != currentMonthDate.month:
            previousMonthPrincipalRepaid = principalRepaid
            principalRepaid = 0
            previousMonthInterestsReceived = interestsReceived
            interestsReceived = 0
            previousMonthCashInGame = currentMonthCashInGame

            currentMonthCashInGame = cashInGame
            currentMonthDate = rowDate
            newMonth = True

        cashInGame = getCashInGame(cashInGame, rowData)

        if rowData['principalRepaid']:
            principalRepaid = principalRepaid + rowData['principalRepaid']
        if rowData['interestReceived']:
            interestsReceived = interestsReceived + rowData['interestReceived']
        if rowData['chargesReceived']:
            interestsReceived = interestsReceived + rowData['chargesReceived']
        if newMonth:
            previousMonthFee = rowData['fee'] or 0.0
            newMonth = False

            # fee is negative number
            if previousMonthCashInGame > 0:
                roi = (previousMonthInterestsReceived + previousMonthFee) / previousMonthCashInGame

            # fee is the last transaction of the previous month
            if currentMonthDate.month - 1 > 0:
                previousMonthYear = currentMonthDate.month - 1, currentMonthDate.year
            else:
                previousMonthYear = 12, currentMonthDate.year - 1

            yield(str(previousMonthYear[0]) + "." + str(previousMonthYear[1]), round(previousMonthCashInGame, 2), round(previousMonthInterestsReceived, 2), round(previousMonthFee, 2), round(roi, 6), round(previousMonthPrincipalRepaid, 2))

    # ongoing month
    # yield(currentMonthDate.strftime('%-m.%Y'), round(cashInGame, 2), round(interestsReceived, 2), '', '', round(principalRepaid, 2))


def getCashFlow():
    for row in getDataFromCSVfile(DATA_FOLDER + LENDY_CSV_FILE):
        rowData = getRowData(row)

        if rowData['cashFlowChange']:
            yield (rowData['rawDate'], rowData['cashFlowChange'])


def main():
    parser = argparse.ArgumentParser(description='This script produces statistics based on Twino\'s exported file.')
    parser.add_argument('-c', '--convert', dest='convert', action='store', default=False, metavar=('CSV_FILENAME'),
                        help='Converting ./data/Lendy_Statement_YYYYMMDD-YYYYMMDD.csv to ./data/lendy.csv')
    parser.add_argument('-f', '--fees', dest='getFees', action='store_true', default=False, help='Paid fees to Zonky')
    parser.add_argument('-t', '--total', dest='getTotals', action='store_true', default=False, help='Account statement')
    parser.add_argument('-tbm', '--totalbymonth', dest='getTotalByMonth', action='store_true', default=False, help='Account statement per month')
    parser.add_argument('-p', '--previousmonth', dest='getPreviousMonth', action='store_true', default=False, help='Account statement for last month')
    parser.add_argument('-cf', '--cashflow', dest='getCashFlow', action='store_true', default=False, help='Cashflow actions within the account')

    args = parser.parse_args()
    resultValues = []

    if args.convert:
        convertToStandardCSV(args.convert)
    elif args.getFees:
        resultValues = getFees()
    elif args.getTotals:
        resultValues = getTotals()
    elif args.getTotalByMonth:
        resultValues = getTotalByMonth()
    elif args.getPreviousMonth:
        resultValues = getPreviousMonth()
    elif args.getCashFlow:
        resultValues = getCashFlow()
    else:
        parser.print_help()

    for list in resultValues:
        print(utils.getTabbedStringFromValueList(list))

    return


if __name__ == '__main__':
    main()