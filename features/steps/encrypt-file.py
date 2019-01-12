import random
import string
from hamcrest import assert_that, not_, contains, equal_to


@given(u"that I have a file in my directory")
def step_impl(context):
    context.test_data = "".join(
        [random.choice(string.ascii_letters + string.digits) for n in range(16)]
    ).encode("utf-8")
    context.test_file_in = "testdata.dat"
    context.test_file_out = "testdata.dat.gpg"
    with open(context.test_file_in, "wb") as data_file:
        data_file.write(context.test_data)


@when(u"I run a script that calls my encryption command on that file")
def step_impl(context):
    context.backup_context.run(["fixtures/encrypt_file.sh"])


@then(u"an encrypted file should be created")
def step_impl(context):
    with open(context.test_file_out, "rb") as data_file:
        context.encrypted_file_contents = data_file.read()
    assert_that(context.encrypted_file_contents, not_(contains(context.test_data)))


@then(u"if I decrypt that file the content should match the original")
def step_impl(context):
    c = context.gpg_context
    plaintext, result, verify_result = c.decrypt(context.encrypted_file_contents)
    assert_that(plaintext, equal_to(context.test_data))
