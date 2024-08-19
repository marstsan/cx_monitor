from datetime import datetime, timedelta
import os

def log_calculator(base_path):
    log_result_file = base_path + "_log_result_" + datetime.today().strftime('%Y-%m-%d') + ".txt"
    filenames = os.listdir(base_path)
    filenames.sort()
    with open(log_result_file, 'w') as outfile:
        outfile.write(f"\n")

    for names in filenames:
        # Open each file in read mode
        passCount = 0
        failCount = 0

        with open(base_path+names, encoding="utf-8") as data:
            passCount = data.read().count("Result: PASSED")
        with open(base_path+names, encoding="utf-8") as data:
            failCount = data.read().count("Result: FAILED")

        totalCount = passCount + failCount
        try:
            passRate = passCount / totalCount * 100
        except ZeroDivisionError:
            passRate = 0
        try:
            failRate = failCount / totalCount * 100
        except ZeroDivisionError:
            failRate = 0

        with open(log_result_file) as orignFile:
            data = orignFile.read()
            new_result_filename = base_path + names
            result = f"<<<<<<<<<<<<<<<<<<<<<<<<<  {names}  >>>>>>>>>>>>>>>>>>>>>>>>\n" \
                     "============================================================================================\n"\
                     + f"  | PASSED : {passCount}  | FAILED : {failCount}  | TOTAL : {totalCount}" \
                     + f"  | PASSED RATE : {passRate:.2f}%" + f"  | FAILED RATE : {failRate:.2f}%" \
                     + "\n============================================================================================\n"
            newdata = data + result
            with open(log_result_file, "w") as out:
                out.write(newdata)

    # yesterday_date = datetime.today() - timedelta(days=1)
    #
    # filename = base_path + "log_calltest_staff2staff_" + datetime.today().strftime('%Y-%m-%d') + ".txt"

    # passCount = 0
    # failCount = 0
    #
    # with open(filename) as data:
    #     passCount = data.read().count("Result: PASSED")
    # with open(filename) as data:
    #     failCount = data.read().count("Result: FAILED")
    #
    # totalCount = passCount + failCount
    # passRate = passCount / totalCount * 100
    # failRate = failCount / totalCount * 100
    #
    #
    # with open(filename) as orignFile:
    #     data = orignFile.read()
    #     result1 = "====================================================" + "\n" \
    #               + f"  | PASSED : {passCount}  | FAILED : {failCount}  | TOTAL : {totalCount}" + "\n"
    #     result2 = "====================================================" + "\n" \
    #               + f"  | PASSED RATE : {passRate:.2f}%" + f"  | FAILED RATE : {failRate:.2f}%" + "\n" \
    #               "====================================================" + "\n"
    #     newdata = result1 + result2 + data
    #     with open(filename, "w") as out:
    #         out.write(newdata)

log_calculator("/home/user/scripts/cx_monitor/log/")
