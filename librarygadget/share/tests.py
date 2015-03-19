import unittest
from django.test import TestCase
from django.test.client import Client
import models
import views

class TestFacebook(TestCase):

	def suite():
		return unittest.makeSuite(TestFacebook,'test')

		
if __name__ == '__main__':
	runner = unittest.TextTestRunner()
	runner.run(suite())

	
