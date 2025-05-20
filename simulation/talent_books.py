import random

def simulate_talent_book_run(domain_level=4):
    """
    Simulates one run of a talent book domain.
    Drop quantities vary by domain level.
    Based on community-sourced averages from Genshin Wiki.
    """
    if domain_level == 1:
        teachings = random.randint(1, 2)
        guides = 1 if random.random() < 0.1 else 0
        philosophies = 0
    elif domain_level == 2:
        teachings = random.randint(2, 3)
        guides = 1 if random.random() < 0.25 else 0
        philosophies = 0
    elif domain_level == 3:
        teachings = random.randint(2, 3)
        guides = random.randint(1, 2)
        philosophies = 1 if random.random() < 0.05 else 0
    elif domain_level == 4:
        teachings = random.randint(2, 3)
        guides = random.randint(1, 3)
        philosophies = 1 if random.random() < 0.10 else 0
    else:
        raise ValueError("Domain level must be between 1 and 4")

    return {
        'Teachings': teachings,
        'Guides': guides,
        'Philosophies': philosophies
    }

def simulate_multiple_talent_runs(runs=3, domain_level=4):
    """
    Simulates multiple talent domain runs at a given domain level.
    """
    total = {'Teachings': 0, 'Guides': 0, 'Philosophies': 0}
    for _ in range(runs):
        result = simulate_talent_book_run(domain_level=domain_level)
        for k in total:
            total[k] += result[k]
    return total
