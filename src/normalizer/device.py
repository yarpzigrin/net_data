from .base import BaseNormalizer
class DeviceNormalizer(BaseNormalizer):
    @classmethod
    def normalize(cls, data, vendor: str):
        # Унификация: speed to int, etc.
        data['speed'] = int(data['speed'].replace('Gbps', '000')) if 'Gbps' in data['speed'] else data['speed']
        return data