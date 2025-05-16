# [i]                                                                                            #
# [i] Libraries                                                                                   #
# [i]                                                                                            #

import os
from dotenv import find_dotenv, load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field


# [i]                                                                                            #
# [i] Settings                                                                                   #
# [i]                                                                                            #

# This class is used to load environment variables from a .env file and make them accessible as attributes.
class Settings(BaseSettings):
    API_KEY: str = Field(validation_alias="API_KEY")
    endpoint: str = Field(validation_alias="endpoint")


# [i]                                                                                            #
# [i] Vars & Instances                                                                           #
# [i]                                                                                            #

# Load environment variables from .env file
# This is crucial for streamlit run, as Pydantic BaseSettings might not load them correctly.
_ = load_dotenv(find_dotenv())
if not _:
    _ = load_dotenv(".env")

print(os.getenv("API_KEY")[0:-15])
print(os.getenv("endpoint"))

local_settings = Settings()