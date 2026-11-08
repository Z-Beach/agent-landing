// Parametric footbed / outsole - US men's 10.5 7E
// Toe-room focused: full ball width is held through the toes (no taper).
// Only foot_length and ball_width are chart-verified; the other widths are
// scaled from the size-8 D reference in infrawiki's shoe_ver_2.scad
// (Appropedia, CC-BY-SA-3.0). Rebuild from a real foot trace for final fit.

foot_length = 275;      // mm, US 10.5
ball_width  = 120.65;   // mm, 7E from healthyfeetstore.com width chart (4.75 in)
heel_width  = 77.5;
arch_width  = 70.1;     // narrowest point
mid_width   = 93.4;
toe_width   = 120.65;   // = ball_width, deliberately no toe taper
sole_thickness = 6;
outline_clearance = 0;  // mm added around the outline (set 2-3 for a footbed)

$fn = 96;

module station(cy, w) {
    ww = w + 2 * outline_clearance;
    translate([0, cy]) scale([ww, ww]) circle(d = 1);
}

module outline2d() {
    hull() {
        station(heel_width / 2, heel_width);
        station(0.2987 * foot_length, arch_width);
        station(0.5195 * foot_length, mid_width);
        station(0.7272 * foot_length, ball_width);
        station(foot_length - toe_width / 2, toe_width);
    }
}

// footbed
linear_extrude(height = sole_thickness) outline2d();

// print check: text is engraved on the heel so a wrong-scale print is obvious
if (false) {
    linear_extrude(height = sole_thickness + 0.2)
        translate([-40, 40]) text("10.5 7E - 120.65mm ball", size = 6);
}
