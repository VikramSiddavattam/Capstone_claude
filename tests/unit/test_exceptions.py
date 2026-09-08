from app.exceptions import (FetchTimeoutError, InvalidUrlError,
                            LocatorLensError, NoElementsFoundError,
                            PageTooLargeError, RenderError, TlsValidationError,
                            TooManyRedirectsError, UnparseableContentError)


def test_locator_lens_error_carries_message():
    error = LocatorLensError("something went wrong")
    assert error.message == "something went wrong"
    assert str(error) == "something went wrong"


def test_all_typed_exceptions_are_locator_lens_errors():
    for exc_cls in (
        InvalidUrlError,
        FetchTimeoutError,
        TlsValidationError,
        UnparseableContentError,
        NoElementsFoundError,
        PageTooLargeError,
        TooManyRedirectsError,
        RenderError,
    ):
        instance = exc_cls("test message")
        assert isinstance(instance, LocatorLensError)
        assert instance.message == "test message"
