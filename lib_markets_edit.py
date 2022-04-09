import pandas
from datetime import datetime


def make_in_play(market_id, column_no, market_type, data, google_sheet):
    markets_df = pandas.DataFrame(google_sheet)
    market_list = list(markets_df[market_type+'_market_id'])
    market_row_no = market_list.index(int(market_id[2:]))+2
    data.update_cell(market_row_no, column_no, "in-play")


def update_position(market_id, column_no, market_type, expected_value, worst_position, data, google_sheet):
    markets_df = pandas.DataFrame(google_sheet)
    market_list = list(markets_df[market_type+'_market_id'])
    market_row_no = market_list.index(int(market_id[2:]))+2
    data.update_cell(market_row_no, column_no, expected_value)
    data.update_cell(market_row_no, column_no+1, worst_position)
    data.update_cell(market_row_no, column_no+2, datetime.now().strftime("%H:%M %d/%m/%Y"))

    # Select a cell range
    #cell_list = data.range('A1:A7')
    #print(chr(ord('A') + column_no-1) + str(market_row_no) + ':' + chr(ord('A') + column_no) + str(market_row_no))
    #cell_list = data.range(chr(ord('A') + column_no-1) + str(market_row_no) + ':' + chr(ord('A') + column_no) + str(market_row_no))
    #print(cell_list)
    # Update values
    #for cell in cell_list:
    #    cell.value = "O_o"

    # Send update in batch mode
    #data.update_cells('[<Cell R8C9 '+expected_value+'>, <Cell R8C10 '+worst_position+'>]')

    #I8:J8
    #[<Cell R8C9 '-£0.17'>, <Cell R8C10 '-£8.00'>]
