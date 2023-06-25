char_name = "Sapporo Jones"
import snoop

from lookup_controller import LookupController


# @snoop
def main():
    l = LookupController(char_name)
    l.lookup()


if __name__ == "__main__":
    main()
