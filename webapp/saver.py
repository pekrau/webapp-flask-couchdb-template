"Base document saver context classes."

import copy
import os.path
import sys

import flask

from . import constants
from . import utils


class BaseSaver:
    "Base document saver context."

    DOCTYPE = None
    EXCLUDE_PATHS = [["_id"], ["_rev"], ["doctype"], ["modified"]]
    HIDDEN_VALUE_PATHS = []

    def __init__(self, doc=None):
        if doc is None:
            self.original = {}
            self.doc = {"_id": utils.get_iuid(),
                        "created": utils.get_time()}
            self.initialize()
        else:
            self.original = copy.deepcopy(doc)
            self.doc = doc
        self.prepare()

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        self.finish()
        self.doc["doctype"] = self.DOCTYPE
        self.doc["modified"] = utils.get_time()
        flask.g.db.put(self.doc)
        self.add_log()

    def __getitem__(self, key):
        return self.doc[key]

    def __setitem__(self, key, value):
        self.doc[key] = value

    def initialize(self):
        "Initialize the new document."
        pass

    def prepare(self):
        "Preparations before making any changes."
        pass

    def finish(self):
        "Final changes and checks on the document before storing it."
        pass

    def wrapup(self):
        """Wrap up the save operation by performing actions that
        must be done after the document has been stored.
        """
        pass

    def add_log(self):
        """Add a log entry recording the the difference betweens the current and
        the original document, hiding values of specified keys.
        'added': list of keys for items added in the current.
        'updated': dictionary of items updated; original values.
        'removed': dictionary of items removed; original values.
        """
        self.stack = []
        diff = self.diff(self.original, self.doc)
        entry = {"_id": utils.get_iuid(),
                 "doctype": constants.DOCTYPE_LOG,
                 "docid": self.doc["_id"],
                 "diff": diff,
                 "timestamp": utils.get_time()}
        self.modify_log_entry(entry)
        if hasattr(flask.g, "current_user") and flask.g.current_user:
            entry["username"] = flask.g.current_user["username"]
        else:
            entry["username"] = None
        if flask.has_request_context():
            entry["remote_addr"] = str(flask.request.remote_addr)
            entry["user_agent"] = str(flask.request.user_agent)
        else:
            entry["remote_addr"] = None
            entry["user_agent"] = os.path.basename(sys.argv[0])
        flask.g.db.put(entry)

    def diff(self, old, new):
        """Find the differences between the old and the new documents.
        Uses a fairly simple algorithm which is OK for shallow hierarchies.
        """
        added = {}
        removed = {}
        updated = {}
        new_keys = set(new.keys())
        old_keys = set(old.keys())
        for key in new_keys.difference(old_keys):
            self.stack.append(key)
            if self.stack not in self.EXCLUDE_PATHS:
                if self.stack in self.HIDDEN_VALUE_PATHS:
                    added[key] = "<hidden>"
                else:
                    added[key] = new[key]
            self.stack.pop()
        for key in old_keys.difference(new_keys):
            self.stack.append(key)
            if self.stack not in self.EXCLUDE_PATHS:
                if self.stack in self.HIDDEN_VALUE_PATHS:
                    removed[key] = "<hidden>"
                else:
                    removed[key] = old[key]
            self.stack.pop()
        for key in new_keys.intersection(old_keys):
            self.stack.append(key)
            if self.stack not in self.EXCLUDE_PATHS:
                new_value = new[key]
                old_value = old[key]
                if isinstance(new_value, dict) and isinstance(old_value, dict):
                    changes = self.diff(old_value, new_value)
                    if changes:
                        if self.stack in self.HIDDEN_VALUE_PATHS:
                            updated[key] = "<hidden>"
                        else:
                            updated[key] = changes
                elif new_value != old_value:
                    if self.stack in self.HIDDEN_VALUE_PATHS:
                        updated[key]= dict(new_value="<hidden>",
                                           old_value="<hidden>")
                    else:
                        updated[key]= dict(new_value= new_value,
                                           old_value=old_value)
            self.stack.pop()
        result = {}
        if added:
            result['added'] = added
        if removed:
            result['removed'] = removed
        if updated:
            result['updated'] = updated
        return result

    def modify_log_entry(self, entry):
        "Modify the log entry, if required."
        pass


class AttachmentsSaver(BaseSaver):
    "Document saver context handling attachments."

    def prepare(self):
        self._delete_attachments = set()
        self._add_attachments = []

    def wrapup(self):
        """Delete any specified attachments.
        Store the input files as attachments.
        Must be done after document is saved.
        """
        for filename in self._delete_attachments:
            rev = flask.g.db.delete_attachment(self.doc, filename)
            self.doc["_rev"] = rev
        for attachment in self._add_attachments:
            flask.g.db.put_attachment(self.doc,
                                      attachment["content"],
                                      filename=attachment["filename"],
                                      content_type=attachment["mimetype"])

    def add_attachment(self, filename, content, mimetype):
        self._add_attachments.append({"filename": filename,
                                      "content": content,
                                      "mimetype": mimetype})

    def delete_attachment(self, filename):
        self._delete_attachments.add(filename)

    def modify_log_items(self, entry):
        "Modify the log entry to add info about attachment changes."
        if self._delete_attachments:
            entry["attachments_deleted"] = self._delete_attachments
        if self._add_attachments:
            for att in self._add_attachments:
                att["size"] = len(att.pop("content"))
            entry["attachments_added"] = self._add_attachments
