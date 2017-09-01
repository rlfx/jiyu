import numpy as np
import talib

def initialize(context):
    # Secuity list
    context.security = sid()

    # Strategy number
    context.SN = 0

    # Buying Price
    context.BP = 0
    
    # Positions info
    context.position_info = []  # [order_price, order_price_dev]
    context.SL = 0 # [stop_loss]
    context.TP = 0 # [target_price]

    
    # BBANDS parameters
    context.BBAND_state = []
    context.BBAND_1dev = 0.9
    context.BBAND_2dev = 2.0
    context.BBAND_d = 30
    schedule_function(info_update,
                      date_rules.every_day(),
                      time_rules.market_open(hours = 1))    
    schedule_function(BBANDS_signal,
                      date_rules.every_day(),
                      time_rules.market_open())
    schedule_function(balance,
                      date_rules.every_day(),
                      time_rules.market_open())
    
def info_update(context, data):
    sec = context.security
    H = data.history(sec, 'high', 90, '1d')
    L = data.history(sec, 'low', 90, '1d')
    C = data.history(sec, 'close', 90, '1d')
    P = C[-1]
    BB_middle = (talib.BBANDS(C, 
                              timeperiod=context.BBAND_d,
                              nbdevup=context.BBAND_1dev, 
                              nbdevdn=context.BBAND_1dev,
                              matype=0)[1])[-1]
    BB1_upper = (talib.BBANDS(C, 
                              timeperiod=context.BBAND_d,
                              nbdevup=context.BBAND_1dev, 
                              nbdevdn=context.BBAND_1dev,
                              matype=0)[0])[-1]
    BB1_lower = (talib.BBANDS(C, 
                              timeperiod=context.BBAND_d,
                              nbdevup=context.BBAND_1dev, 
                              nbdevdn=context.BBAND_1dev,
                              matype=0)[2])[-1]
    BB2_upper = (talib.BBANDS(C, 
                              timeperiod=context.BBAND_d,
                              nbdevup=context.BBAND_2dev, 
                              nbdevdn=context.BBAND_2dev,
                              matype=0)[0])[-1]
    BB2_lower = (talib.BBANDS(C, 
                              timeperiod=context.BBAND_d,
                              nbdevup=context.BBAND_2dev, 
                              nbdevdn=context.BBAND_2dev,
                              matype=0)[2])[-1]
    S = context.BBAND_state[-11:-1]
    if context.portfolio.positions[sec].amount and context.SN == 1:
        context.TP = BB2_upper
        context.SL = 0.95*BB1_lower
        if P >= BB2_upper:
            context.SL = 0.5*(BB1_upper+BB2_upper)
            context.TP = 0.9*BB2_upper
	if context.portfolio.positions[sec].amount and context.SN == 2:
		context.TP = BB2_upper
        context.SL = 0.95*BB1_upper
        if P >= BB2_upper:
            context.SL = 0.5*(BB1_upper+BB2_upper)
            context.TP = 0.9*BB2_upper
            
def balance(context, data):
    sec = context.security
    H = data.history(sec, 'high', 90, '1d')
    L = data.history(sec, 'low', 90, '1d')
    C = data.history(sec, 'close', 90, '1d')
    P = C[-1]
    S = context.BBAND_state[-11:-1]
    if context.portfolio.positions[sec].amount:

        if S.count(2) + S.count(3) > 8:
        	order_target_percent(sec, 0)
        	context.SN = 0
        	print('REACH TOP HIGH', P-context.BP)
        	context.BP = 0 
    	if P <= context.SL:
        	order_target_percent(sec, 0)
        	context.SN = 0
        	print('REACH SL', P-context.BP)
        	context.BP = 0 
    	if P >= context.TP:
        	order_target_percent(sec, 0)
        	context.SN = 0
        	print('REACH TP', P-context.BP)
        	context.BP = 0 
        if S.count(1) > 6:
            order_target_percent(sec, 0)
            context.SN = 0
            print('not Strong enough in 1-2', P-context.BP)
            context.BP = 0
def BBANDS_signal(context, data):
    sec = context.security
    O = data.history(sec, 'open', 90, '1d')
    C = data.history(sec, 'close', 90, '1d')
    P = C[-1]
    BB_middle = (talib.BBANDS(C, 
                              timeperiod=context.BBAND_d,
                              nbdevup=context.BBAND_1dev, 
                              nbdevdn=context.BBAND_1dev,
                              matype=0)[1])[-1]
    BB1_upper = (talib.BBANDS(C, 
                              timeperiod=context.BBAND_d,
                              nbdevup=context.BBAND_1dev, 
                              nbdevdn=context.BBAND_1dev,
                              matype=0)[0])[-1]
    BB1_lower = (talib.BBANDS(C, 
                              timeperiod=context.BBAND_d,
                              nbdevup=context.BBAND_1dev, 
                              nbdevdn=context.BBAND_1dev,
                              matype=0)[2])[-1]
    BB2_upper = (talib.BBANDS(C, 
                              timeperiod=context.BBAND_d,
                              nbdevup=context.BBAND_2dev, 
                              nbdevdn=context.BBAND_2dev,
                              matype=0)[0])[-1]
    BB2_lower = (talib.BBANDS(C, 
                              timeperiod=context.BBAND_d,
                              nbdevup=context.BBAND_2dev, 
                              nbdevdn=context.BBAND_2dev,
                              matype=0)[2])[-1]
    if C[-1] > BB2_upper:
        context.BBAND_state.append(3)
    elif C[-1] > BB1_upper:
        context.BBAND_state.append(2)
    elif C[-1] > BB_middle:
        context.BBAND_state.append(1)
    elif C[-1] > BB1_lower:
        context.BBAND_state.append(-1)
    elif C[-1] > BB2_lower:
        context.BBAND_state.append(-2)
    elif C[-1 ] > BB2_lower:
        context.BBAND_state.append(-3)

    S = context.BBAND_state[-11:-1]
    # LONG SINGNAL 
    # STRATEGY 1: 過去10天有超過8天state都在 -1 or -2 & P>mid時買 
    if S.count(-1) + S.count(-2) >7 and P > BB_middle:
        if context.portfolio.positions[sec].amount == 0:
            order_target_percent(sec, 1.0)
            log.info('1 LONG')
            context.BP = P
            context.SN = 1
            context.SL = 0.95*BB1_lower
            context.TP = BB2_upper
    # STRATEGY 2
    if S.count(-2) + S.count(-1) + S.count(1) > 7 and P > BB1_upper:
        if context.portfolio.positions[sec].amount == 0:
            order_target_percent(sec, 1)
            log.info('2 LONG')
            context.BP = P
            context.SN = 2
            context.SL = 0.95*BB1_upper
            context.TP = BB2_upper
    # STRATEGY 3 
    # if S.count(1) + S.count(-1) >7 and P < BB1_lower:
    #     if context.portfolio.positions[sec].amount == 0:
    #         order_target_percent(sec, 1)
    #         log.info('3 SHORT')
    #         context.BP = P
    #         context.SN = 3
    #         context.SL = 1.05*BB1_lower
    #         context.TP = BB2_lower
    record(PRICE = C[-1],
           B_MID = BB_middle,
           BB1_LOW = BB1_lower,
           BB2_LOW = BB2_lower)