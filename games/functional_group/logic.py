from rdkit import Chem
from rdkit.Chem import Draw, RWMol
import random
import os
import uuid
import glob

# Functional groups with SMARTS
functional_groups = {
    "Alcohol": "[OX2H][#6]",
    "Amine": "[NX3;H2,H1;!$(NC=O)]",
    "Ketone": "[CX3](=O)[#6]",
    "Aldehyde": "[CX3H1](=O)",
    "Carboxyl": "C(=O)[OX2H1]",
    "Ester": "[CX3](=O)O[#6]",
    "Amide": "C(=O)N",
    "Ether": "[OD2]([#6])[#6]",
    "Thiol": "[SX2H]",
    "Thioether": "[#6]-S-[#6]",
    "Peptide": "C(=O)N[C]",   # stricter than Amide
    "Halide": "[F,Cl,Br,I]"
}

# Side chains
side_chains = {"Methyl": 1, "Ethyl": 2, "Propyl": 3, "Butyl": 4}
side_chain_weights = {"Methyl": 40, "Ethyl": 30, "Propyl": 20, "Butyl": 10}


# --- Utility functions ---
def atom_can_attach(mol, atom_idx, new_bonds):
    atom = mol.GetAtomWithIdx(atom_idx)
    current_valence = sum([b.GetBondTypeAsDouble() for b in atom.GetBonds()])
    max_valence = Chem.GetPeriodicTable().GetDefaultValence(atom.GetAtomicNum())
    return current_valence + new_bonds <= max_valence


def generate_basic_scaffold(structure_type="chain", length=4):
    if structure_type == "chain":
        mol = RWMol()
        atoms = [mol.AddAtom(Chem.Atom(6)) for _ in range(length)]
        for i in range(length - 1):
            mol.AddBond(atoms[i], atoms[i + 1], Chem.BondType.SINGLE)
        return mol, atoms

    if structure_type == "cycloalkane":
        mol = RWMol()
        atoms = [mol.AddAtom(Chem.Atom(6)) for _ in range(length)]
        for i in range(length):
            mol.AddBond(atoms[i], atoms[(i + 1) % length], Chem.BondType.SINGLE)
        return mol, atoms

    if structure_type == "aromatic":
        benzene = Chem.MolFromSmiles("c1ccccc1")
        mol = RWMol(benzene)
        atoms = list(range(mol.GetNumAtoms()))
        return mol, atoms

    # Fallback
    benzene = Chem.MolFromSmiles("c1ccccc1")
    mol = RWMol(benzene)
    atoms = list(range(mol.GetNumAtoms()))
    return mol, atoms


def cleanup_generated_images(base_dir=None, keep=0):
    if base_dir is None:
        base_dir = os.path.dirname(__file__)

    out_dir = os.path.join(base_dir, "static", "generated")
    os.makedirs(out_dir, exist_ok=True)

    files = sorted(glob.glob(os.path.join(out_dir, "*.png")), key=os.path.getmtime)
    if keep < 0:
        keep = 0

    if keep == 0:
        files_to_delete = files
    else:
        files_to_delete = files[:-keep] if len(files) > keep else []

    for file_path in files_to_delete:
        try:
            os.remove(file_path)
        except OSError:
            pass


def attach_functional_group(mol, main_atoms, fg_name):
    fg_smarts = Chem.MolFromSmarts(functional_groups[fg_name])
    bonds_needed = {
        "Alcohol": 1, "Amine": 1, "Ketone": 2, "Aldehyde": 2,
        "Carboxyl": 3, "Ester": 3, "Amide": 3, "Ether": 2,
        "Thiol": 1, "Thioether": 2, "Peptide": 3, "Halide": 1
    }[fg_name]

    valid_atoms = [a for a in main_atoms if atom_can_attach(mol, a, bonds_needed)]
    if not valid_atoms:
        return None, None

    attach_atom = random.choice(valid_atoms)
    rw_mol = RWMol(mol)

    try:
        if fg_name == "Alcohol":
            o_idx = rw_mol.AddAtom(Chem.Atom(8))
            rw_mol.AddBond(attach_atom, o_idx, Chem.BondType.SINGLE)

        elif fg_name == "Amine":
            n_idx = rw_mol.AddAtom(Chem.Atom(7))
            rw_mol.AddBond(attach_atom, n_idx, Chem.BondType.SINGLE)

        elif fg_name == "Ketone":
            o_idx = rw_mol.AddAtom(Chem.Atom(8))
            rw_mol.AddBond(attach_atom, o_idx, Chem.BondType.DOUBLE)

        elif fg_name == "Aldehyde":
            o_idx = rw_mol.AddAtom(Chem.Atom(8))
            rw_mol.AddBond(main_atoms[0], o_idx, Chem.BondType.DOUBLE)

        elif fg_name == "Carboxyl":
            o1 = rw_mol.AddAtom(Chem.Atom(8))
            o2 = rw_mol.AddAtom(Chem.Atom(8))
            rw_mol.AddBond(attach_atom, o1, Chem.BondType.DOUBLE)
            rw_mol.AddBond(attach_atom, o2, Chem.BondType.SINGLE)

        elif fg_name == "Ester":
            c = rw_mol.AddAtom(Chem.Atom(6))
            o = rw_mol.AddAtom(Chem.Atom(8))
            rw_mol.AddBond(attach_atom, c, Chem.BondType.DOUBLE)
            rw_mol.AddBond(c, o, Chem.BondType.SINGLE)

        elif fg_name == "Amide":
            o = rw_mol.AddAtom(Chem.Atom(8))
            n = rw_mol.AddAtom(Chem.Atom(7))
            rw_mol.AddBond(attach_atom, o, Chem.BondType.DOUBLE)
            rw_mol.AddBond(attach_atom, n, Chem.BondType.SINGLE)

        elif fg_name == "Ether":
            o = rw_mol.AddAtom(Chem.Atom(8))
            c = rw_mol.AddAtom(Chem.Atom(6))
            rw_mol.AddBond(attach_atom, o, Chem.BondType.SINGLE)
            rw_mol.AddBond(o, c, Chem.BondType.SINGLE)

        elif fg_name == "Thiol":
            s_idx = rw_mol.AddAtom(Chem.Atom(16))
            rw_mol.AddBond(attach_atom, s_idx, Chem.BondType.SINGLE)

        elif fg_name == "Thioether":
            s_idx = rw_mol.AddAtom(Chem.Atom(16))
            c_idx = rw_mol.AddAtom(Chem.Atom(6))
            rw_mol.AddBond(attach_atom, s_idx, Chem.BondType.SINGLE)
            rw_mol.AddBond(s_idx, c_idx, Chem.BondType.SINGLE)

        elif fg_name == "Peptide":
            c_idx = rw_mol.AddAtom(Chem.Atom(6))
            o_idx = rw_mol.AddAtom(Chem.Atom(8))
            n_idx = rw_mol.AddAtom(Chem.Atom(7))
            c_side = rw_mol.AddAtom(Chem.Atom(6))
            rw_mol.AddBond(attach_atom, c_idx, Chem.BondType.SINGLE)
            rw_mol.AddBond(c_idx, o_idx, Chem.BondType.DOUBLE)
            rw_mol.AddBond(c_idx, n_idx, Chem.BondType.SINGLE)
            rw_mol.AddBond(n_idx, c_side, Chem.BondType.SINGLE)

        elif fg_name == "Halide":
            hal_idx = rw_mol.AddAtom(Chem.Atom(random.choice([9, 17, 35, 53])))
            rw_mol.AddBond(attach_atom, hal_idx, Chem.BondType.SINGLE)

        Chem.SanitizeMol(rw_mol)

        if rw_mol.HasSubstructMatch(fg_smarts):
            highlight_atoms = rw_mol.GetSubstructMatch(fg_smarts)
            return rw_mol, highlight_atoms

        return None, None

    except Exception:
        return None, None


def attach_side_chain(mol, main_atoms, sc_name):
    rw_mol = RWMol(mol)
    chain_length = side_chains[sc_name]
    valid_atoms = [a for a in main_atoms if atom_can_attach(rw_mol, a, chain_length)]
    if not valid_atoms:
        return None, None

    attach_atom = random.choice(valid_atoms)
    chain_atoms = []
    prev_idx = attach_atom

    for _ in range(chain_length):
        c_idx = rw_mol.AddAtom(Chem.Atom(6))
        rw_mol.AddBond(prev_idx, c_idx, Chem.BondType.SINGLE)
        chain_atoms.append(c_idx)
        prev_idx = c_idx

    return rw_mol, chain_atoms


# --- Detect overlapping functional groups ---
def detect_overlapping_fg(mol, current_fg, highlight_atoms):
    composite_groups = ["Carboxyl", "Ester", "Peptide", "Amide"]
    for fg in composite_groups:
        smarts = Chem.MolFromSmarts(functional_groups[fg])
        if mol.HasSubstructMatch(smarts):
            highlight_atoms = mol.GetSubstructMatch(smarts)
            return fg, highlight_atoms
    return current_fg, highlight_atoms


def generate_random_molecule(max_attempts=20):
    """
    Returns: (mol, highlight_fg, highlight_atoms_total, options)
    """
    for _ in range(max_attempts):
        try:
            scaffold_type = random.choices(
                ["chain", "cycloalkane", "aromatic"],
                weights=[35, 35, 30]
            )[0]

            length = random.randint(2, 10)
            mol, atoms = generate_basic_scaffold(scaffold_type, length)

            fg_weights = [10, 15, 15, 10, 10, 10, 9, 8, 7, 5, 15, 5]
            fg_list = random.choices(
                list(functional_groups.keys()),
                weights=fg_weights,
                k=random.choice([1, 2, 3])
            )

            highlight_fg = random.choice(fg_list)
            highlight_atoms_total = []

            for fg in fg_list:
                mol, highlight_atoms = attach_functional_group(mol, atoms, fg)
                if mol is None:
                    continue
                if fg == highlight_fg:
                    highlight_atoms_total = highlight_atoms

            if random.random() < 0.3:
                sc_name = random.choices(
                    list(side_chains.keys()),
                    weights=list(side_chain_weights.values())
                )[0]
                mol, sc_atoms = attach_side_chain(mol, atoms, sc_name)
                if mol is not None and random.random() < 0.5:
                    highlight_fg = sc_name
                    highlight_atoms_total = sc_atoms

            highlight_fg, highlight_atoms_total = detect_overlapping_fg(
                mol, highlight_fg, highlight_atoms_total
            )

            options = list(functional_groups.keys()) + list(side_chains.keys())
            random.shuffle(options)

            return mol, highlight_fg, highlight_atoms_total, options

        except Exception:
            continue

    mol = Chem.MolFromSmiles("CCO")
    return mol, "Alcohol", [0, 1, 2], list(functional_groups.keys()) + list(side_chains.keys())


def render_molecule_png(mol, highlight_atoms, size=(300, 300)):
    """
    Saves a generated molecule image into this blueprint's static/generated folder.
    Returns a relative path like: "generated/quiz_<id>.png"
    """
    # Save under: games/functional_group/static/generated/
    base_dir = os.path.dirname(__file__)
    out_dir = os.path.join(base_dir, "static", "generated")
    os.makedirs(out_dir, exist_ok=True)

    filename = f"quiz_{uuid.uuid4().hex}.png"
    out_path = os.path.join(out_dir, filename)

    d2d = Draw.MolDraw2DCairo(size[0], size[1])

    if mol is None:
        mol = Chem.MolFromSmiles("CCO")
        highlight_atoms = [0, 1, 2]

    d2d.DrawMolecule(mol, highlightAtoms=highlight_atoms if highlight_atoms else None)
    d2d.FinishDrawing()

    with open(out_path, "wb") as f:
        f.write(d2d.GetDrawingText())

    # IMPORTANT: this is relative to the blueprint static folder
    return f"generated/{filename}"


def generate_quiz_round():
    """
    Convenience function for your route:
    Generates a molecule, renders png, returns:
      (img_relpath, correct_answer, options)
    """
    mol, fg_name, highlight_atoms, options = generate_random_molecule()
    img_relpath = render_molecule_png(mol, highlight_atoms)
    return img_relpath, fg_name, options
