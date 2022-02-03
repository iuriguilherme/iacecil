#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  ia.cecil
#  
#  Copyleft 2012-2022 Iuri Guilherme <https://iuri.neocities.org/>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  

import iacecil, logger, sys, uvicorn
logger = logging.getLogger(iacecil.name)

if __name__ == '__main__':
    ### Default args
    bot = 'iacecil'
    mode = 'quart'
    port = 8000
    host = '127.0.0.1'
    log_level = 'info'
    reload = True
    canonical = None
    
    ### Args parsing
    if len(sys.argv) > 1:
        logger.info(u"Setting operation MODE to {}".format(mode))
        mode = sys.argv[1]
        if len(sys.argv) > 2:
            bot = sys.argv[2]
            logger.info(
            u"Using configuration from bot \"{}\" from config file.\
            ".format(bot)
            )
            if len(sys.argv) > 3:
                logger.info(u"Setting PORT to {}".format(port))
                port = sys.argv[3]
                if len(sys.argv) > 4:
                    logger.info(u"Setting HOST to {}".format(host))
                    host = sys.argv[4]
                    if len(sys.argv) > 5:
                        logger.info(u"Setting LOG level to {}\
                        ".format(log_level))
                        log_level = sys.argv[5]
                        if len(sys.argv) > 6:
                            logger.info(u"Setting RELOAD to {}\
                            ".format(str(reload)))
                            reload = bool(sys.argv[6])
                            if len(sys.argv) > 7:
                                logger.info(u"Setting CANONICAL to {}\
                                ".format(str(canonical)))
                                canonical = str(sys.argv[7])
        else:
            logger.warning(u"Bot name not informed, assuming {}\
                ".format(bot))
    else:
        logger.warning(u"Operation mode not informed, assuming {}\
            ".format(mode))
    ### Running scripts
    logger.basicConfig(level = log_level)
    if mode == 'quart':
        try:
            logger.info(u"Starting {}".format(iacecil.actual_name))
            app = iacecil.get_app(bot.split(','))
            setattr(app, 'canonical', canonical)
            uvicorn.run(
                app,
                host = host,
                port = int(port),
                log_level = log_level,
            )
            logger.info(u"Finishing {}".format(iacecil.actual_name))
        except Exception as e:
            logger.critical(repr(e))
            logger.warning(u"Finishing with error {}...\
            ".format(iacecil.actual_name))
            raise
    elif mode == 'socket':
        try:
            logger.info(u"Starting {}".format(iacecil.actual_name))
            app = iacecil.get_app(bot.split(','))
            setattr(app, 'canonical', canonical)
            uvicorn.run(
                app,
                uds = 'uvicorn.sock',
                forwarded_allow_ips = '*',
                proxy_headers = True,
                timeout_keep_alive = 0,
                log_level = log_level,
            )
            logger.info(u"Finishing {}".format(iacecil.actual_name))
        except Exception as e:
            logger.critical(repr(e))
            logger.warning(u"Finishing with error {}...\
            ".format(iacecil.actual_name))
            raise
    elif mode == 'block':
        try:
            logger.info(u"Starting {}".format(iacecil.actual_name))
            app = iacecil.get_app(bot.split(','))
            setattr(app, 'canonical', canonical)
            iacecil.run_app(app)
            logger.info(u"Finishing {}".format(iacecil.actual_name))
        except Exception as e:
            logger.critical(repr(e))
            logger.warning(u"Finishing with error {}...\
            ".format(iacecil.actual_name))
            raise
    elif mode == 'dev':
        try:
            logger.info(u"Starting {}".format(iacecil.actual_name))
            uvicorn.run(
                'iacecil:app',
                host = host,
                port = int(port),
                log_level = log_level,
                reload = reload,
            )
            logger.info(u"Finishing {}".format(iacecil.actual_name))
        except Exception as e:
            logger.critical(repr(e))
            logger.warning(u"Finishing with error {}...\
            ".format(iacecil.actual_name))
            raise
    else:
        logger.info(u"Wrong operation mode. RTFM will you please. Bye.")
else:
    logger.info(u"RTFM")
