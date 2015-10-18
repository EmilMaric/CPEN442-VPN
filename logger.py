import datetime


class Logger(object):

    @staticmethod
    def log(msg, machine_type):
        time = datetime.datetime.now().time().strftime('%H:%M')
        info_msg = "(%s) [(%s)] " % (time, machine_type)
        info_msg += msg
        print info_msg
