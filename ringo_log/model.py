import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from ringo.model import Base
from ringo.model.base import BaseItem, BaseFactory
from ringo.lib.helpers import serialize
from ringo.model.mixins import Mixin, Owned, Meta


class LogFactory(BaseFactory):

    def create(self, user=None):
        new_item = BaseFactory.create(self, user)
        return new_item


class Log(BaseItem, Owned, Meta, Base):
    """Docstring for log extension"""

    __tablename__ = 'logs'
    """Name of the table in the database for this modul. Do not
    change!"""
    _modul_id = None
    """Will be set dynamically. See include me of this modul"""

    # Define columns of the table in the database
    id = sa.Column(sa.Integer, primary_key=True)
    author = sa.Column('author', sa.Text, nullable=True, default=None)
    """Textual representation of the user. This will even stay if the
    origin creator (user) is deleted."""
    category = sa.Column('category', sa.Integer, nullable=True, default=None)
    subject = sa.Column('subject', sa.Text, nullable=False, default=None)
    text = sa.Column('text', sa.Text, nullable=True, default=None)

    @classmethod
    def get_item_factory(cls):
        return LogFactory(cls)


class Logged(Mixin):
    """Mixin to add logging functionallity to a modul. Adding this Mixin
    the item of a modul will have a "logs" relationship containing all
    the log entries for this item. Log entries can be created
    automatically by the system or may be created manual by the user.
    Manual log entries. Needs to be configured (Permissions)"""

    @declared_attr
    def logs(cls):
        tbl_name = "nm_%s_logs" % cls.__name__.lower()
        nm_table = sa.Table(tbl_name, Base.metadata,
                            sa.Column('iid', sa.Integer,
                                      sa.ForeignKey(cls.id)),
                            sa.Column('lid', sa.Integer,
                                      sa.ForeignKey("logs.id")))
        logs = sa.orm.relationship(Log, secondary=nm_table, cascade="all")
        return logs

    def build_changes(self, old_values, new_values):
        """Returns a dictionary with the old and new values for each
        field which has changed"""
        diff = {}
        for field in new_values:
            oldv = serialize(old_values.get(field))
            newv = serialize(new_values.get(field))
            if newv == oldv:
                continue
            if field == "data":
                diff[field] = {"old": oldv, "new": newv}
            else:
                diff[field] = {"old": serialize(oldv), "new": serialize(newv)}
        return diff

    def add_log_entry(self, subject, text, request):
        """Will add a log entry for the updated item.
        The mapper and the target parameter will be the item which
        iherits this logged mixin.

        :request: Current request
        :subject: Subject of the logentry.
        :text: Text of the logentry.

        """
        factory = Log.get_item_factory()
        log = factory.create(user=request.user)
        log.subject = subject
        log.text = text
        log.author = str(request.user)
        self.logs.append(log)
