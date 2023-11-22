import sys

print(sys.argv)

# very dirty way to work around PyCharm's inability to pass arguments to test runner
# this problem only occurs if you run scripts in Python tests conf
sys.argv.append("_tests/sheet-1-valid.data.csv")
sys.argv.append("_tests/output-results/")

print(sys.argv)