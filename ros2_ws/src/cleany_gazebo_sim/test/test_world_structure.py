from pathlib import Path
from xml.etree import ElementTree


WORLD_PATH = (
    Path(__file__).resolve().parents[1] / 'worlds' / 'cleany_mecanum_prototype.sdf'
)


def test_world_contains_dual_arm_joint_skeleton():
    root = ElementTree.parse(WORLD_PATH).getroot()
    model = root.find("./world/model[@name='cleany_mecanum']")
    assert model is not None

    links = {link.attrib['name'] for link in model.findall('link')}
    joints = {joint.attrib['name'] for joint in model.findall('joint')}

    assert {
        'left_arm_base',
        'left_moving_jaw',
        'right_arm_base',
        'right_moving_jaw',
    } <= links
    assert {
        'left_rotation_l_joint',
        'left_jaw_joint',
        'right_rotation_r_joint',
        'right_jaw_joint',
    } <= joints


def test_world_reuses_mujoco_mesh_resource_uris():
    root = ElementTree.parse(WORLD_PATH).getroot()
    mesh_uris = {uri.text for uri in root.findall('.//mesh/uri')}

    assert 'model://assets/raskogbody.stl' in mesh_uris
    assert 'model://assets/Base.stl' in mesh_uris
    assert 'model://assets/Moving_Jaw.stl' in mesh_uris
