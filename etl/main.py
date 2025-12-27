"""Main module for the ETL process of extracting and processing card data."""

import logging

from services.data_service import DataService
from util import print_splash, BColors, GAME_PATH, NUM_THREADS, clear_directory


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s|%(name)s|%(levelname)s]: %(message)s",
    )
    logger = logging.getLogger("main")

    print_splash()
    DONE_MESSAGE = BColors.OKCYAN + "Done" + BColors.ENDC

    logger.info(
        '%sGame path: "%s"%s',
        BColors.OKCYAN,
        GAME_PATH,
        BColors.ENDC,
    )
    logger.info(
        "%sThreads to use: %d%s",
        BColors.OKCYAN,
        NUM_THREADS,
        BColors.ENDC,
    )

    data_service = DataService()

    logger.info("Getting ids...")
    data_service.get_ids()
    logger.info(DONE_MESSAGE)

    logger.info("Getting card names...")
    data_service.get_card_data()
    logger.info(DONE_MESSAGE)

    # logger.info("Cleaning data...")
    # data_service.clean_data()
    # logger.info(DONE_MESSAGE)

    # logger.info("Writing data...")
    # data_service.write_data()
    # logger.info(DONE_MESSAGE)

    # logger.info("Removing temporary files...")
    # clear_directory("./etl/services/temp")
    # logger.info(DONE_MESSAGE)

    logger.info("%sETL Finished%s", BColors.OKGREEN, BColors.ENDC)
