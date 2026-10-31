from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock
from tool import execute

class ExpansionTests(TestCase):
    def test_shrink_rejected_without_patch(self):
        client=Mock()
        client.get.return_value={'metadata':{'name':'disk'},'spec':{'resources':{'requests':{'storage':'100Gi'}}}}
        with self.assertRaises(ValueError):execute(client,SimpleNamespace(name='disk',expand_size='50Gi',apply=True))
        client.patch.assert_not_called()
    def test_storage_class_must_allow_expansion(self):
        client=Mock()
        client.get.side_effect=[{'metadata':{'name':'disk'},'spec':{'storageClassName':'fast','resources':{'requests':{'storage':'100Gi'}}}}, {'allowVolumeExpansion':False}]
        with self.assertRaises(ValueError):execute(client,SimpleNamespace(name='disk',expand_size='200Gi',apply=True))
        client.patch.assert_not_called()
