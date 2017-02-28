import scala.io.Source

case class DataTuple(val objectId : String, val name: String, val state: String, val pyRevenue : Long, val cyRevenue: Long ) {

  override def toString: String = {
    return s"$name : [ $pyRevenue, $cyRevenue ]"
  }

  def computeYoY(): Double = {
    return ( this.cyRevenue - this.pyRevenue ) * 1.0 / this.pyRevenue
  }

}

object DataTuple {
  def apply( str: String ): DataTuple ={
    val tokens = str.split(",")
    try {
      DataTuple( tokens(0), tokens(1), tokens(2), tokens(3).toLong, tokens(4).toLong )
    } catch {
      case e : Exception =>
        println(str)
        null
    }
  }
}



def main(): Unit ={
  val filename    = args(0)
  val revenueData = Source.fromFile(filename)
    .getLines
    .map( l => DataTuple(l) )
    .filter(  c => c.pyRevenue > 0 & c.cyRevenue > 0 )
    .toList

  println(s"Loading ${revenueData.length} items")

  val yoyRevenue = revenueData.map{ c => (c.state, c.computeYoY()) }

  val totalYoYRevenue = yoyRevenue.map(_._2).sum / yoyRevenue.length
  val states = yoyRevenue
    .groupBy(_._1)
    .map{ st => (st._1, st._2.map(_._2).sum / st._2.length ) }
    .toList
    .sortBy(- _._2) // order in descending order
    .map{ st =>
    st._1 + " : " + st._2
  }


  println(s"Total national average YoY Revenue in 2013 : $totalYoYRevenue")
  println("---- Average YoY by State --")
  println(states.mkString("\n"))
}

main()
