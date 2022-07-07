from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from client import pokemon_client
from misc import (get_english_genus, get_english_name_of,
                  get_default_pokemon_from_species,
                  get_thumb_url, get_formatted_typing)
import script
import const


def create_datapage_text(species, is_expanded=False):
    data = dict()
    pokemon = get_default_pokemon_from_species(species)
    data['name'] = get_english_name_of(species)
    data['artwork_link'] = get_thumb_url(pokemon)
    data['types'] = get_formatted_typing(pokemon)
    data['abilities'] = get_formatted_abilities(pokemon)
    data['hidden_ability'] = get_formatted_abilities(pokemon, hidden_ability=True)
    types = [t.type.name for t in pokemon.types]
    data['primary_type'] = types[0]
    data['secondary_type'] = types[1] if len(types) > 1 else 'no'
    data['evolution_family'] = get_formatted_evolution_chain(species)
    data['stats'] = {stat.stat.name: stat.base_stat for stat in pokemon.stats}
    data['stats_rating'] = get_stats_rating_emoji(data['stats'])
    if is_expanded:
        data['genus'] = get_english_genus(species.genera)
        data['dex_number'] = species.order
        data['height'] = str(pokemon.height / 10) + ' m'
        data['weight'] = str(pokemon.weight / 10) + ' kg'
        data['gender_percentage'] = get_gender_percentage(species)
        data['base_friendship'] = species.base_happiness
        ev_yield = {get_short_stat_name(stat.stat.name): stat.effort for stat in pokemon.stats if stat.effort != 0}
        data['ev_yield_text'] = " / ".join([str(ev_yield[stat]) + " " + stat for stat in ev_yield])
        data['catch_rate'] = species.capture_rate
        data['growth_rate'] = species.growth_rate.name.title().replace("-", " ")
        egg_groups = [group.name.title().replace("-", " ") for group in species.egg_groups]
        data['egg_groups_text'] = " / ".join(egg_groups)
        data['egg_cycles'] = species.hatch_counter
    return script.pokemon_page(data)


def get_formatted_abilities(pokemon, hidden_ability=False):
    abilities = get_abilities(pokemon, hidden_ability)
    return ' / '.join(abilities)


def get_abilities(pokemon, hidden_ability=False):
    ability_list = list()
    for ability in pokemon.abilities:
        ability_text = ability.ability.name.title().replace('-', ' ')
        if hidden_ability == ability.is_hidden:
            ability_list.append(ability_text)
    return ability_list


def get_formatted_evolution_chain(species):
    chain = get_chain_obj(species)
    chain_dict = prettify_chain(chain)
    if len(chain_dict) == 1:
        return '<i>It is not known to evolve into or from any other Pokémon</i>\n'
    stage_index = 1
    text = ''
    for stage in chain_dict:
        stage_name = chain_dict[stage]['name']
        method = chain_dict[stage]['method']
        if species.name == stage:
            stage_name = stage_name.join(['<u>', '</u>'])
        arrow_prefix = add_arrows_scheme(stage_index)
        text += f'{arrow_prefix}{stage_name} {method}\n'
        stage_index += 1
    return text


def get_chain_obj(species):
    chain_url = species.evolution_chain.url
    chain_id = chain_url.split('/').pop(-2)
    chain = pokemon_client.get_evolution_chain(chain_id).pop().chain
    return chain


def prettify_chain(chain, pre_evolution=None):
    species = pokemon_client.get_pokemon_species(chain.species.name).pop()
    species_name = get_english_name_of(species)
    methods = get_evolution_method(chain.evolution_details)
    chain_dict = {
        species.name: {
            'name': species_name,
            'pre_evolution': pre_evolution,
            'method': methods
        }
    }
    if 'evolves_to' in dir(chain):
        for stage in chain.evolves_to:
            chain_dict.update(prettify_chain(stage, pre_evolution=species_name))
    return chain_dict


def get_evolution_method(method_list):
    method_text_list = list()
    for method in method_list:
        method_text_list.append('{} {}'.format(
            serialize_trigger(method.trigger.name),
            serialize_condition(method)
        ))
    if not method_text_list: return ''
    return '({})'.format(' / '.join(method_text_list))


def serialize_trigger(trigger):
    if trigger == 'level-up': return 'Level'
    if trigger == 'use-item': return 'Use'
    if trigger == 'trade': return 'Trade'
    if trigger == 'shed': return script.shedinja_method
    if trigger == 'spin': return script.alcremie_method
    if trigger == 'tower-of-darkness': return script.urshifu_method
    if trigger == 'tower-of-waters': return script.urshifu_method
    if trigger == 'three-critical-hits': return script.sirfetch_method
    if trigger == 'take-damage': return script.runerigus_method


def serialize_condition(method):
    condition_list = list()
    if method.trigger.name == 'level-up':
        if method.min_level: condition_list.append(str(method.min_level))
        else: condition_list.append('up')
    if method.min_happiness: condition_list.append('with high happiness')
    if method.min_beauty: condition_list.append('with high beauty')
    if method.min_affection: condition_list.append('with high affection')
    if method.needs_overworld_rain: condition_list.append('during rain')
    if method.relative_physical_stats == 1: condition_list.append('if Attack > Defense')
    if method.relative_physical_stats == -1: condition_list.append('if Attack < Defense')
    if method.relative_physical_stats == 0: condition_list.append('if Attack = Defense')
    if method.turn_upside_down: condition_list.append(script.malamar_method)
    if method.time_of_day: condition_list.append('during ' + method.time_of_day.title())
    if method.trade_species: condition_list.append('with ' + method.trade_species.name.title())
    if method.known_move_type: condition_list.append('knowing a {} move'.format(method.known_move_type.name.title()))
    if method.party_type: condition_list.append('with a {} Pokémon in the party'.format(method.party_type.name.title()))
    if method.gender: condition_list.append('[only female]' if method.gender == 1 else '[only male]')
    if method.item:
        item = pokemon_client.get_item(method.item.name).pop()
        condition_list.append(get_english_name_of(item))
    if method.held_item:
        item = pokemon_client.get_item(method.held_item.name).pop()
        condition_list.append('holding ' + get_english_name_of(item))
    if method.known_move:
        move = pokemon_client.get_move(method.held_item.name).pop()
        condition_list.append('knowing ' + get_english_name_of(move))
    if method.location:
        location = pokemon_client.get_location(method.location.name).pop()
        condition_list.append('in ' + get_english_name_of(location))
    if method.party_species:
        species = pokemon_client.get_pokemon_species(method.party_species.name).pop()
        condition_list.append('with {} in the party'.format(species))
    return ' '.join(condition_list)


def add_arrows_scheme(stage_index):
    if stage_index == 1: return ''
    if stage_index == 2: return '↳ '
    if stage_index == 3: return '   ↳ '


def get_stats_rating_emoji(stats_dict):
    emoji_dict = {}
    for stat in stats_dict:
        stat_value = stats_dict[stat]
        if stat_value < 20: rating_emoji = const.RED_CIRCLE
        elif stat_value < 50: rating_emoji = const.ORANGE_CIRCLE * 2
        elif stat_value < 80: rating_emoji = const.YELLOW_CIRCLE * 3
        elif stat_value < 100: rating_emoji = const.GREEN_CIRCLE * 4
        elif stat_value < 130: rating_emoji = const.BLUE_CIRCLE * 5
        else: rating_emoji = const.PURPLE_CIRCLE * 6
        emoji_dict[stat] = rating_emoji
    return emoji_dict


def get_gender_percentage(species):
    if species.gender_rate == -1:
        return "Genderless"
    else:
        female = species.gender_rate / 8 * 100
        male = 100 - female
        return f"{male}% / {female}%"


def get_short_stat_name(stat):
    if stat == "hp": return "HP"
    if stat == "attack": return "ATK"
    if stat == "defense": return "DEF"
    if stat == "special-attack": return "SPA"
    if stat == "special-defense": return "SPD"
    if stat == "speed": return "SPE"


def create_datapage_markup(species_name, is_expanded=False):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text=script.reduce if is_expanded else script.expand,
                callback_data=f'infos/{int(not is_expanded)}/{species_name}'
            )
        ], [
            InlineKeyboardButton(
                text=script.moveset,
                callback_data=f'moveset/1/{species_name}'
                # 1 => page number, 10 moves each page (see set_moveset())
            )
        ], [
            InlineKeyboardButton(
                text=script.location,
                callback_data=f'locations/{species_name}'
            )
        ]
    ])