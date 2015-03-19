# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'UserProfile'
        db.create_table('librarybot_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('api_key', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('account_level', self.gf('django.db.models.fields.CharField')(default='free', max_length=10)),
            ('paid_last_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('paid_first_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal('librarybot', ['UserProfile'])

        # Adding model 'Library'
        db.create_table('librarybot_library', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('catalogurl', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('librarysystem', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('renew_supported_code', self.gf('django.db.models.fields.CharField')(default='untested', max_length=10)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('lastmodified', self.gf('django.db.models.fields.DateField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('librarybot', ['Library'])

        # Adding model 'Patron'
        db.create_table('librarybot_patron', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('library', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['librarybot.Library'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('patronid', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('pin', self.gf('django.db.models.fields.CharField')(max_length=75)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150, null=True)),
            ('save_history', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('lastchecked', self.gf('django.db.models.fields.DateTimeField')()),
            ('batch_last_run', self.gf('django.db.models.fields.DateField')(null=True)),
        ))
        db.send_create_signal('librarybot', ['Patron'])

        # Adding model 'Item'
        db.create_table('librarybot_item', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('patron', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['librarybot.Patron'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('outDate', self.gf('django.db.models.fields.DateField')(null=True)),
            ('dueDate', self.gf('django.db.models.fields.DateField')(null=True)),
            ('timesRenewed', self.gf('django.db.models.fields.SmallIntegerField')(null=True)),
            ('isbn', self.gf('django.db.models.fields.CharField')(max_length=25, null=True)),
            ('asof', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('librarybot', ['Item'])

        # Adding model 'AccessLog'
        db.create_table('librarybot_accesslog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('patron', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['librarybot.Patron'])),
            ('library', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['librarybot.Library'])),
            ('viewfunc', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('error', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('error_stacktrace', self.gf('django.db.models.fields.CharField')(max_length=3000)),
            ('date', self.gf('django.db.models.fields.DateField')(auto_now=True, null=True, blank=True)),
        ))
        db.send_create_signal('librarybot', ['AccessLog'])

        # Adding model 'LibraryRequest'
        db.create_table('librarybot_libraryrequest', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('libraryname', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('catalogurl', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('patronid', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('librarybot', ['LibraryRequest'])

        # Adding model 'RenewalResponse'
        db.create_table('librarybot_renewalresponse', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('token', self.gf('django.db.models.fields.CharField')(max_length=36)),
            ('response', self.gf('django.db.models.fields.TextField')()),
            ('cachedate', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('librarybot', ['RenewalResponse'])


    def backwards(self, orm):
        
        # Deleting model 'UserProfile'
        db.delete_table('librarybot_userprofile')

        # Deleting model 'Library'
        db.delete_table('librarybot_library')

        # Deleting model 'Patron'
        db.delete_table('librarybot_patron')

        # Deleting model 'Item'
        db.delete_table('librarybot_item')

        # Deleting model 'AccessLog'
        db.delete_table('librarybot_accesslog')

        # Deleting model 'LibraryRequest'
        db.delete_table('librarybot_libraryrequest')

        # Deleting model 'RenewalResponse'
        db.delete_table('librarybot_renewalresponse')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'librarybot.accesslog': {
            'Meta': {'object_name': 'AccessLog'},
            'date': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'error': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'error_stacktrace': ('django.db.models.fields.CharField', [], {'max_length': '3000'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'library': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['librarybot.Library']"}),
            'patron': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['librarybot.Patron']"}),
            'viewfunc': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'librarybot.item': {
            'Meta': {'object_name': 'Item'},
            'asof': ('django.db.models.fields.DateField', [], {}),
            'author': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'dueDate': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isbn': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True'}),
            'outDate': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'patron': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['librarybot.Patron']"}),
            'timesRenewed': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        'librarybot.library': {
            'Meta': {'object_name': 'Library'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'catalogurl': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastmodified': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'}),
            'librarysystem': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'renew_supported_code': ('django.db.models.fields.CharField', [], {'default': "'untested'", 'max_length': '10'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        'librarybot.libraryrequest': {
            'Meta': {'object_name': 'LibraryRequest'},
            'catalogurl': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'libraryname': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'patronid': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        'librarybot.patron': {
            'Meta': {'object_name': 'Patron'},
            'batch_last_run': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastchecked': ('django.db.models.fields.DateTimeField', [], {}),
            'library': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['librarybot.Library']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True'}),
            'patronid': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '75'}),
            'save_history': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'librarybot.renewalresponse': {
            'Meta': {'object_name': 'RenewalResponse'},
            'cachedate': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response': ('django.db.models.fields.TextField', [], {}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '36'})
        },
        'librarybot.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'account_level': ('django.db.models.fields.CharField', [], {'default': "'free'", 'max_length': '10'}),
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'paid_first_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'paid_last_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['librarybot']
