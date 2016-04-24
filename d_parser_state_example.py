example_state = {
    'game': {
        'current_level': 4,  # Текущий уровень
    },
    'level': {
        'codes_left': 10,  # Осталось кодов
        'spoiler_taken': False,
        'sector_list': [
            {
                'name': 'Основные коды',
                'code_list': [
                    {
                        'ko': '1+',
                        'taken': False,  # Взят ли код?
                    },
                    {
                        'ko': '1',
                        'taken': True,
                    },
                    {
                        'ko': '3',
                        'taken': True,
                    }
                ]
            },
            {
                'name': 'Бонусные коды',
                'code_list': [
                    {
                        'ko': '2+',
                        'taken': False,
                    },
                    {
                        'ko': '4',
                        'taken': False,
                    }
                ]
            }
        ]
    }
}
