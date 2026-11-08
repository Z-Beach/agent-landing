// Steve Helminen
// MY4777 - Michigan Technological University
// Source: https://www.appropedia.org/File:Shoe_ver_2_Scad.scad (CC-BY-SA-3.0)
// All dimensions are in mm
// Distances from center to cross section
a = 34.925;
b = a + 38.1;
c = b + 53.975;
d = c + 50.8;
e = 244.475;
step = 0;


$fn=50;

union() {
//Forming the sole of the shoe:
	difference (){
		linear_extrude(height = 10) {
			hull() {

			// Back of the foot (heal)
			translate([0,31.5,0])
			circle(d= 63,center = true);

			//Cross Section #1 of foot (heel)
			translate([0,a,0])
			circle(d = 63.5, center = true);

			//Cross Section #2 of foot (shortest distance of arch)
			translate([0,b,0])
			circle(d= 57.15,center = true);

			//Cross Section #3 of foot (Widening section between shortest distance and the balls of your feet
			translate([0,c,0])
			circle(d= 76.2,center = true);

			translate([0,d,0])
			circle(d= 100,center = true);

			translate([0,e-50,0])
			circle(d= 100,center = true);

			}
		
		}

			//Cutting sections in the bottom of the shoe for flexibility
			for(i=[0:20]) {
			translate([0, c+(i*8), 3])
			cube(size = [75,4,6], center = true);
			}
	}


//Ankle Support
	difference() {
	translate ([0,31.5,37.5])
	cylinder(h = 75, d1 = 72, d2 = 72, center = true);

		//Section Cuts out of ankle main
		translate ([0,31.5,37.5])
		cylinder(h = 75, d1 = 63 , d2 = 63, center = true);

		translate ([0,50,50])
		cube(size = [150,75,100], center = true);
	



		}

}

// Strap attachment point
// Side supports
difference() {			
				rotate([0,0,90]){
				translate ([d,(95.25/2),41.275/2])
				cube(size = [45,8,41.275], center = true);
				}
			
				//Cut out of foot geometry
				translate([0,d,35])
				cylinder(h = 50, d= 98,center = true);

				translate([-7,d,48])
				cube(size = [80,80,80],center = true);
				
}
difference() {
				rotate([0,0,90]){
				translate ([d,(-95.25/2),41.275/2])
				cube(size = [45,8,41.275], center = true);
				}
			
				//Cut out of foot geometry
				translate([0,d,35])
				cylinder(h = 50, d= 98,center = true);

				translate([7,d,48])
				cube(size = [80,80,80],center = true);
}
