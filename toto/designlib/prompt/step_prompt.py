"""
    <name> 
       toto_layout/prompt/step_prompt.py

    <description>
        Contains the prompt functions/dispatcher to handle commands provided
        by a user to edit a step. 

        Check go_to_step_prompt for details on how this dispatcheer works

    <author>
        Santiago Torres-Arias

    <date>
        09/27/2016
""" 
import sys

from prompt_toolkit import prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from toto.designlib.history import history
from toto.designlib.util import TotoCommandCompletions, print_help

from toto.models.layout import Step

PROMPT = unicode("toto-layout/{}->step({})> ")


def leave(*args):
    """:
            Leave the Toto layout tool 
    """

    message = unicode("You er editing a step, "
                      "are you  sure you want to leave? [Y/n]")
    yesorno = prompt(message)

    if yesorno.startswith("Y"):
        sys.exit()


def add_material_matchrule(layout, step, args):
    """ (MATCH|CREATE|MODIFY|DELETE) <path> [from=<stepname>] :
            Add a matchrule to this step. the MATCH key requires the "from"
            argument
    """
    # FIXME: we should validate this
    if len(args) <=2:
        print("We can't create a step without a name")
        return False

    step.material_matchrules.append(" ".join(args))
    return False

def list_material_matchrules(layout, step, args):
    """:
            List the existing material matchrules in this step
    """
    i = 0
    for matchrule in step.material_matchrules:
        print("{:3}: {}".format(i, matchrule))
        i += 1

    return False

def remove_material_matchrule(layout, step, args):
    """ <number>:
            Remove matchrule numbered <number>
    """
    if (len(args) < 1):
        list_material_matchrules(step, [])
        print("\nWhich matchrule do you want to delete?")
        text = prompt()
        target = int(text)
    else:
        target = args[0]

    # FIXME: some bound checking here would be interesting here
    step.material_matchrules.remove(target)

    return False

def add_product_matchrule(layout, step, args):
    """ (MATCH|CREATE|MODIFY|DELETE) <path> [from=<stepname>] :
            Add a matchrule to this step's product matchrules. The MATCH key
            requires the "from" argument
    """
    # FIXME: we should validate this
    if len(args) < 2:
        return False

    name = args[0]
    step.product_matchrules.append(" ".join(args))

    return False

def list_product_matchrules(layout, step, args):
    """: 
            List the product matchrules in this step
    """
    i = 0
    for matchrule in step.product_matchrules:
        print("{:3}: {}".format(i, matchrule))
        i += 1

    return False

def remove_product_matchrule(layout, step, args):
    """ <number>:
            Remove the product matchrule numbered <number>
    """
    if (len(args) < 1):
        list_product_matchrules(step, [])
        print("\nWhich matchrule do you want to delete?")
        text = prompt()
        target = int(text)
    else:
        target = args[0]

    # FIXME: some bound checking here would be interesting here
    step.product_matchrules.remove(target)

    return False

def set_expected_command(layout, step, args):
    """ <path>:
            Load the pubkey from <path> and add it as a functionary pubkey
    """
    if not args:
        print("We need to have *something* as an expected command :/")
        return False

    step.expected_command = " ".join(args)
    return False


def add_pubkey(layout, step, args):
    """ <keyid>:
            Add the functionary pubkey with keyid <keyid>, A prefix can be 
            be used instead of the whole keyid (it must be the only matching 
            prefix)
    """
    if len(args) < 1:
        print("We need the functionary's keyid  to add it to this step!")
        return

    keyid = args[0]

    for key in layout.keys:
        if key['keyid'] == keyid:
            break
    else:
        print("Couldn't find the key!")

    step.pubkeys.append(keyid)
    print("Successfully added pubkey to this step.")
    return False


def remove_pubkey(layout, step, args):
    """ <keyid>:
            Remove the functionary pubkey with keyid <keyid>, A prefix can be 
            be used instead of the whole keyid (it must be the only matching 
            prefix)
    """
    if len(args) < 1:
        print("We require the keyid you want to remove from this step")
        return

    target_keyid = args[0]

    for keyid in step.pubkeys:
        if keyid == target_keyid:
            layout.keys.remove(keyid)
            break
    else:
        print("Couldn't find this keyid!")

    print("Successfuly removed key from step")
    return False

def list_pubkeys(layout, step, args):
    """: 
            List the functionary pubkeys that can sign for this step
    """
    for keyid in step.pubkeys:
        print(keyid)
    return False

def go_back(layout, step, args):
    """:  
            Finish editing this step and go back
    """
    # here, we verify that we have a proper step, or prompt for force
    return True

def list_functionary_pubkeys(layout, step, args):
    """:
            List the available pubkeys for this layout
    """
    i = 1
    for key in layout.keys:
        print("[{}]({}) {}".format(i, key['keytype'], key['keyid']))

# a dictionary with function pointers to the handlers of this class
VALID_COMMANDS = {
        "add_product_matchrule":  add_product_matchrule,
        "list_product_matchrules": list_product_matchrules,
        "remove_product_matchrule": remove_product_matchrule,
        "add_material_matchrule": add_material_matchrule,
        "list_material_matchrules": list_material_matchrules,
        "remove_material_matchrule": remove_material_matchrule,
        "set_expected_command": set_expected_command,
        "add_pubkey": add_pubkey,
        "remove_pubkey": remove_pubkey,
        "list_pubkeys": list_pubkeys,
        "list_available_pubkeys": list_functionary_pubkeys,
        "exit": leave,
        "back": go_back,
        "help": print_help,
    }

def go_to_step_prompt(layout, name, edit=False):
    """ 
        <name>
            go_to_step_prompt

        <description>
            This function handles the user queries. It does so by loading the 
            VALID_COMMANDS strucutre above (that contains function pointers),
            pre-sanitizing input and callind the appropriate command handler.

        <return>
            Once go_back is called, a populated step object is returned to the
            caller (tentatively, the layout-handling prompt)

        <side-effects>
            None
    """

    # setup the environment and eye candy 
    thisprompt = PROMPT.format("layout", name)
    completer = TotoCommandCompletions(VALID_COMMANDS.keys(), layout, [])

    # find the step to edit or create
    if edit:
        for this_step in layout.steps:
            if this_step.name == name:
                step = this_step
                break
        else:
            print("Could not find a step named {} for editing".format(name))
            return None
    else:
        print("Creating step... {}".format(name))
        step = Step(name=name)

    while True:

        text = prompt(thisprompt, history=history, 
                     auto_suggest=AutoSuggestFromHistory(),
                     completer=completer)

        command = text.split()

        if command[0] not in VALID_COMMANDS:
            print("You've input a wrong command")
            continue

        # do generic dispatching
        if command[0] == "help":
            print_help(VALID_COMMANDS)
            continue


        should_go_back = VALID_COMMANDS[command[0]](layout, step, command[1:])
        if should_go_back:
            break

    return step
