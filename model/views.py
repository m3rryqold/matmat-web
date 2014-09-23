import colorsys
from django.shortcuts import render
from lazysignup.decorators import allow_lazy_user
import math
from model.models import UserSkill, Skill


NAMES = ('numbers', 'addition', 'subtraction', 'multiplication', 'division')


@allow_lazy_user
def my_skills(request, pk=None):
    get_user_skill_value.clear()    # clear cache for skill value getter

    active = "numbers"

    data = {}
    skills = []
    for name in NAMES:
        skill = Skill.objects.get(name=name)
        getter = globals()['my_skills_' + name]
        data[skill] = getter(request.user)
        skill.style = get_style(data[skill]["skill"])
        skills.append(skill)
        if pk in skill.children_list.split(","):
            active = name

    return render(request, 'model/my_skills.html', {
        "data": data,
        "skills": skills,
        "active": active,
    })


def get_user_skills(user, parent_list):
    skills = Skill.objects.filter(parent__name__in=parent_list)
    skills_name = set([s.name for s in skills])
    user_skills = {k: None for k in skills_name}
    for us in UserSkill.objects.filter(user=user.pk, skill__in=skills)\
            .select_related("skill"):
        user_skills[us.skill.name] = us
        # compute skill from parents:
        us.value = us.value + get_user_skill_value(user, us.skill.parent_id)
        us.value_percent = int(100. / (1 + math.exp(-us.value)))
        us.style = get_style(us)
    return user_skills


def get_user_skill_by_name(name, user):
    user_skill = UserSkill.objects.filter(user=user, skill__name=name)
    if len(user_skill) == 1:
        user_skill = user_skill[0]
        # compute skill from parents:
        user_skill.value = user_skill.value +\
            get_user_skill_value(user, user_skill.skill.parent_id)
        user_skill.value_percent = \
            int(100. / (1 + math.exp(-user_skill.value)))
        user_skill.style = get_style(user_skill)
    else:
        user_skill = None

    return user_skill


def memoize(f):
    """ Memoization decorator for functions taking one or more arguments. """
    class memodict(dict):
        def __init__(self, f):
            self.f = f

        def __call__(self, *args):
            return self[args]

        def __missing__(self, key):
            ret = self[key] = self.f(*key)
            return ret

    return memodict(f)


@memoize
def get_user_skill_value(user, skill):
    """
    compute absolute skill of user
    """

    skill = Skill.objects.get(pk=skill)
    user_skill = UserSkill.objects.get(user=user, skill=skill)

    # stop recursion on root
    if skill.parent is None:
        if user_skill is None:
            return 0
        else:
            return user_skill.value

    # initialize skill if does not exist
    if user_skill is None:
        user_skill = 0

    parent_user_skill_value = get_user_skill_value(user, skill.parent_id)
    return user_skill.value + parent_user_skill_value


def my_skills_numbers(user):
    user_skills = get_user_skills(user, ['numbers <= 10', 'numbers <= 20',
                                         'numbers <= 100'])

    return {
        "table": [[get_skill_repr(str(c + r * 10), user_skills)
                   for c in range(1, 11)] for r in range(2)],
        "skills": get_user_skills(user, ["numbers"]),
        "skill": get_user_skill_by_name("numbers", user),
    }


def my_skills_addition(user):
    user_skills = get_user_skills(user, ['addition <= 10', 'addition <= 20'])
    return {
        "table": [[get_skill_repr('%s+%s' % (c, r), user_skills)
                   for c in range(1, 11)] for r in range(1, 21)],
        "skills": get_user_skills(user, ["addition"]),
        "skill": get_user_skill_by_name("addition", user),
    }


def my_skills_subtraction(user):
    user_skills = get_user_skills(user, ['subtraction <= 10',
                                         'subtraction <= 20'])
    return {
        "table": [[get_skill_repr('%s-%s' % (r, c), user_skills)
                   for c in range(1, r + 1)] for r in range(1, 21)],
        "skills": get_user_skills(user, ["subtraction"]),
        "skill": get_user_skill_by_name("subtraction", user),
    }


def my_skills_multiplication(user):
    user_skills = get_user_skills(user, ['multiplication1', 'multiplication2'])
    return {
        "table": [[get_skill_repr('%sx%s' % (c, r), user_skills)
                   for c in range(11)] for r in range(21)],
        "skills": get_user_skills(user, ["multiplication"]),
        "skill": get_user_skill_by_name("multiplication", user),
    }


def my_skills_division(user):
    user_skills = get_user_skills(user, ['division1'])
    return {
        "table": [[get_skill_repr('%s/%s' % (a * b, b), user_skills)
                  for a in range(11)] for b in range(1, 11)],
        "skills": get_user_skills(user, ["division"]),
        "skill": get_user_skill_by_name("division", user),
    }


def get_skill_repr(name, user_skills):
    if name in user_skills:
        return {'name': name, 'style': get_style(user_skills[name])}
    else:
        return {'name': '', 'style': get_style(None, name)}


def get_style(user_skill, name=None):
    ''' return css style of user skill'''
    if user_skill is None:
        if name is None:
            return 'background-color: rgba(127, 127, 0, 0.2);'
        return 'background-color: rgba(127, 127, 0, 0);'

    value = (1 / (1 + math.exp(-user_skill.value)))
    color = colorsys.hsv_to_rgb(1./12 + value * 2 / 9., 1, 0.8)
    color = [int(c*255) for c in color]
    return "background-color: rgba({0[0]}, {0[1]}, {0[2]}, 1);".format(color)
