from typing import Annotated
from pydantic import BeforeValidator

def normalise_string(string: any)-> any:
    """ Returns lowercased and stripped white space string """
    if isinstance(string,str):
        return string.strip().lower()
    return string

normalised_string = Annotated[str, BeforeValidator(normalise_string)]
optional_normalised_string = Annotated[str | None, BeforeValidator(normalise_string)]