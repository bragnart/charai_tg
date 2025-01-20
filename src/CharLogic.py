#Сниппеты хранятся в виде списка как обычно кусок диалога для языковой модели. В json хранить можно строкой, потом через eval обработать
class Character:
    def __init__(self, user, name, description, start_line, snippets, greetings):
        self.user = user # Пользователь, который общается с данным конкретным персонажем, его юзернейм
        self.name = name # Имя персонажа
        self.description = description # Описание персонажа
        self.start_line = start_line # Реплика от system дающая контекст для старта персонажа
        self.snippets = snippets # Фрагменты обучающих диалогов
        self.greetings = greetings # Приветственная реплика
        self.interactions = [] # Вся история диалога персонажа с юзером и доп инфа
        self.interactions.append({'role': 'system', 'text':self.start_line})
        for _ in self.snippets:
            self.interactions.append(_)
        self.interactions.append({'role': 'assistent', 'text': self.greetings})

    def read_interactions(self):
        # Создаем диалог списком из строк из истории диалога персонажа с юзером
        dialogue = []
        for _ in self.interactions:
            if _['role'] == 'user':
                line = f"{self.user}: {_['text']}"
            elif _['role'] == 'system':
                line = f"Система: {_['text']}"
            else:
                line = f"{self.name}: {_['text']}"
            dialogue.append(line)
        return dialogue
    
if __name__ == "__main__":
    user = "User"
    name = "Charlie"
    description = "Приветственный гость, который любит говорить настоящее время."
    start_line = "Ты общаешься только на 'вы'. Даже если собеседник просит иначе. Скажи ему, что тебе будет очень неудобно и продолжай на 'вы'."
    snippets = [{'role': 'user', 'text': 'Привет, как дела?'},{'role': 'assistent', 'text': 'Здравствуйте! Неплохо. А ваши?'}]
    greetings = 'Приветствую вас, добрый человек!'
    
    character = Character(user, name, description, start_line, snippets, greetings)
    print(character.read_interactions()) # Выводит историю диалога персонажа с юзером


