from django.test import TestCase
from mock import MagicMock, patch

from . import BillingAddressStep, ShippingStep
from ..checkout import Checkout, STORAGE_SESSION_KEY
from ..checkout.steps import BaseAddressStep
from ..userprofile.models import Address

NEW_ADDRESS = {
    'first_name': 'Test',
    'last_name': 'Test',
    'street_address_1': 'Test',
    'city': 'Test',
    'postal_code': '987654',
    'country': 'PL'}


class TestBaseAddressStep(TestCase):

    def setUp(self):
        self.request = MagicMock()
        self.request.user.is_authenticated.return_value = False
        self.checkout = MagicMock()
        self.address = Address()

    def test_new_method(self):
        '''
        Test the BaseAddressStep managment form when method is set to 'new'
        and user isn't authenticated.
        '''
        self.request.POST = NEW_ADDRESS.copy()
        step = BaseAddressStep(self.request, {}, self.address)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')
        self.assertEqual(step.address.first_name, 'Test')


class TestBillingAddressStep(TestCase):

    def setUp(self):
        self.request = MagicMock()
        self.request.user.is_authenticated.return_value = False
        self.request.POST = NEW_ADDRESS.copy()
        self.request.POST['email'] = 'test@example.com'
        self.checkout = MagicMock()

    def test_address_save_without_address(self):
        storage = {}
        step = BillingAddressStep(self.request, storage)
        self.assertEquals(step.process(), None)
        self.assertEqual(type(storage['address']), Address)
        self.assertEqual(storage['address'].first_name, 'Test')

    def test_address_save_with_address_in_checkout(self):
        storage = {'address': Address()}
        step = BillingAddressStep(self.request, storage)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')


class TestShippingStep(TestCase):

    def setUp(self):
        self.request = MagicMock()
        self.request.user.is_authenticated.return_value = False
        self.request.session = {}
        self.checkout = MagicMock()
        self.checkout.get_group.return_value = {}
        self.checkout.billing_address = None

    @patch.object(Address, 'save')
    def test_address_save_without_address(self, mock_save):
        self.request.POST = NEW_ADDRESS.copy()
        self.request.POST['method'] = 'dummy_shipping'
        self.request.session = {STORAGE_SESSION_KEY: {}}
        group = MagicMock()
        group.address = None
        storage = {}
        step = ShippingStep(self.request, storage, group)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')
        step.save()
        self.assertEqual(mock_save.call_count, 0)
        self.assertEqual(type(storage['address']), Address,
                         'Address instance expected')

    @patch.object(Address, 'save')
    def test_address_save_with_address_in_group(self, mock_save):
        self.request.POST = NEW_ADDRESS.copy()
        self.request.POST['method'] = 'dummy_shipping'
        group = MagicMock()
        group.address = Address()
        storage = {}
        step = ShippingStep(self.request, storage, group)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')
        step.save()
        self.assertEqual(mock_save.call_count, 0)

    @patch.object(Address, 'save')
    def test_address_save_with_address_in_checkout(self, mock_save):
        self.request.POST = NEW_ADDRESS.copy()
        self.request.POST['method'] = 'dummy_shipping'
        original_billing_address_data = {'first_name': 'Change',
                                         'last_name': 'Me',
                                         'id': 10}
        original_billing_address = Address(**original_billing_address_data)
        group = MagicMock()
        group.address = None
        storage = {'address': original_billing_address}
        step = ShippingStep(self.request, storage, group)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')
        step.save()
        self.assertEqual(mock_save.call_count, 0)
        self.assertEqual(storage['address'],
                         Address(**NEW_ADDRESS))
        self.assertEqual(storage['address'].id, None)
