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

try:
    if __name__ == '__main__':
        import iacecil, logging, sys, uvicorn
        log_level = 'info'
        if len(sys.argv) > 1:
            log_level = sys.argv[1]
        logging.basicConfig(level = getattr(logging, log_level.upper()))
        logger = logging.getLogger(iacecil.name)
        
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
            log_level = sys.argv[1]
            logger.info(u"Setting LOG level to {}\
            ".format(log_level))
            if len(sys.argv) > 2:
                mode = sys.argv[2]
                logger.info(u"Setting operation MODE to {}".format(
                    mode)
                )
                if len(sys.argv) > 3:
                    bot = sys.argv[3]
                    logger.info(u"""Using configuration from BOT "{}" f\
rom config file.""".format(bot))
                    if len(sys.argv) > 4:
                        port = sys.argv[4]
                        logger.info(u"Setting PORT to {}".format(port))
                        if len(sys.argv) > 5:
                            host = sys.argv[5]
                            logger.info(u"Setting HOST to {}".format(
                                host)
                            )
                            if len(sys.argv) > 6:
                                reload = bool(sys.argv[6])
                                logger.info(u"Setting RELOAD to {}\
                                ".format(str(reload)))
                                if len(sys.argv) > 7:
                                    canonical = str(sys.argv[7])
                                    logger.info(
                                        u"Setting CANONICAL to {}\
                                        ".format(str(canonical))
                                    )
                else:
                    logger.warning(u"BOT name not informed, assuming {}\
                        ".format(bot))
            else:
                logger.warning(
                    u"Operation MODE not informed, assuming {}".format(
                        mode)
                )
        else:
            logger.warning(u"Logging level not informed, assuming {}\
                ".format(log_level))
        ### Running scripts
        if mode == 'quart':
            try:
                logger.info(u"Starting {}".format(iacecil.actual_name))
                app = iacecil.get_app(bot.split(','), log_level.upper())
                setattr(app, 'log_level', log_level.upper())
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
                app = iacecil.get_app(bot.split(','), log_level.upper())
                setattr(app, 'log_level', log_level.upper())
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
                app = iacecil.get_app(bot.split(','), log_level.upper())
                setattr(app, 'log_level', log_level.upper())
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
except:
    print(u"RTFM")
    raise
